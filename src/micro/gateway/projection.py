import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

import httpx2
from pydantic import JsonValue
from pydantic_core import from_json
from starlette.requests import Request
from starlette.responses import Response

from micro._microservices import Microservice, StoreClient, apply_state_atomically
from micro.queue import QueueClient, QueueDelivery

from ._gateway import ConnectionEventKind


@dataclass(frozen=True, slots=True)
class ProjectedObject:
  kind: str
  id: str
  guild_id: str | None
  payload: dict[str, JsonValue]
  deleted: bool = False


class GatewayProjection(Microservice):
  """Maintains connection-owned Discord state from queued raw dispatches."""

  def __init__(
    self,
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
    batch_size: int = 100,
  ) -> None:
    if not 1 <= batch_size <= 1000:
      raise ValueError("batch_size must be between 1 and 1000.")
    self.store = StoreClient(transport=transport, timeout=timeout)
    self.queue = QueueClient(transport=transport, timeout=timeout)
    self._batch_size = batch_size
    self._topology_ready = asyncio.Event()
    self._tasks: list[asyncio.Task[None]] = []
    self._pending: asyncio.Queue[QueueDelivery] = asyncio.Queue(batch_size * 2)
    super().__init__("gateway.projection")
    self.add_route(
      "/projection/connections/{connection_id}",
      self._delete_connection,
      methods=("DELETE",),
      name="gateway.projection:delete-connection",
    )

  @property
  def component_ready(self) -> bool:
    return self.store.state_revision >= 0 and self.queue.state_revision >= 0

  def apply_state(self, state: JsonValue) -> None:
    apply_state_atomically((self.store, self.queue), state)
    self._topology_ready.set()

  async def start(self) -> None:
    self._tasks = [
      asyncio.create_task(self._consume(), name="micro.gateway.project.consume"),
      asyncio.create_task(self._project_batches(), name="micro.gateway.project.batch"),
    ]

  async def close(self) -> None:
    for task in self._tasks:
      task.cancel()
    await asyncio.gather(*self._tasks, return_exceptions=True)
    self._tasks.clear()
    await self.store.aclose()
    await self.queue.aclose()

  async def project_event(self, item: bytes) -> None:
    await self.project_events((item,))

  async def project_events(self, items: tuple[bytes, ...]) -> None:
    projected_by_key: dict[tuple[str, str, str], ProjectedObject] = {}
    for item in items:
      connection_id, name, payload = _decode_projection_event(item)
      for projected in _project_dispatch(name, payload):
        key = (connection_id, projected.kind, projected.id)
        previous = projected_by_key.get(key)
        if previous is not None and not previous.deleted and not projected.deleted:
          projected = ProjectedObject(
            projected.kind,
            projected.id,
            projected.guild_id or previous.guild_id,
            _merge_json(previous.payload, projected.payload),
          )
        projected_by_key[key] = projected
    if not projected_by_key:
      return

    keys = tuple(projected_by_key)
    query_declarations: list[str] = []
    query_fields: list[str] = []
    query_variables: dict[str, JsonValue] = {}
    for index, (connection_id, kind, object_id) in enumerate(keys):
      query_declarations.extend(
        (f"$connection{index}: ID!", f"$kind{index}: String!", f"$id{index}: ID!")
      )
      query_fields.append(
        f"object{index}: projectionDiscordObject(connectionId: $connection{index}, "
        f"kind: $kind{index}, id: $id{index}) {{ payload }}"
      )
      query_variables.update(
        {
          f"connection{index}": connection_id,
          f"kind{index}": kind,
          f"id{index}": object_id,
        }
      )
    existing = await self._execute(
      f"query Existing({', '.join(query_declarations)}) {{ {' '.join(query_fields)} }}",
      query_variables,
    )

    declarations = list(query_declarations)
    variables = dict(query_variables)
    fields: list[str] = []
    for index, key in enumerate(keys):
      projected = projected_by_key[key]
      if projected.deleted:
        fields.append(
          f"delete{index}: deleteDiscordObject(connectionId: $connection{index}, "
          f"kind: $kind{index}, id: $id{index})"
        )
        continue
      current = existing.get(f"object{index}")
      payload = projected.payload
      if isinstance(current, dict) and isinstance(current.get("payload"), dict):
        payload = _merge_json(
          cast(dict[str, JsonValue], current["payload"]), projected.payload
        )
      declarations.extend((f"$guild{index}: ID", f"$payload{index}: JSON!"))
      variables[f"guild{index}"] = projected.guild_id
      variables[f"payload{index}"] = payload
      operation = (
        "updateDiscordObject" if isinstance(current, dict) else "createDiscordObject"
      )
      fields.append(
        f"write{index}: {operation}(connectionId: $connection{index}, "
        f"kind: $kind{index}, id: $id{index}, guildId: $guild{index}, "
        f"payload: $payload{index}) {{ id }}"
      )
      if not isinstance(current, dict):
        fields.append(
          f"attach{index}: attachDiscordObject(connectionId: $connection{index}, "
          f"kind: $kind{index}, id: $id{index})"
        )
    await self._execute(
      f"mutation Project({', '.join(declarations)}) {{ {' '.join(fields)} }}",
      variables,
    )

  async def project_connection(self, item: bytes) -> None:
    decoded = from_json(item)
    if (
      not isinstance(decoded, list)
      or len(decoded) != 4
      or decoded[0] != "connection"
      or not isinstance(decoded[1], str)
      or isinstance(decoded[2], bool)
      or not isinstance(decoded[2], int)
      or (decoded[3] is not None and not isinstance(decoded[3], str))
    ):
      raise ValueError(
        "Connection events must be [connection, kind, shard_id, connection_id]."
      )
    kind = ConnectionEventKind(decoded[1])
    shard_id = decoded[2]
    connection_id = decoded[3]
    if connection_id is None:
      return
    if kind is ConnectionEventKind.READY:
      existing = await self._execute(
        "query Connection($id: ID!) { gatewayConnection(id: $id) { id } }",
        {"id": connection_id},
      )
      if existing.get("gatewayConnection") is None:
        await self._execute(
          """
          mutation Ready($id: ID!, $shard: Int!, $state: String!) {
            createGatewayConnection(id: $id, shardId: $shard, active: true, state: $state) { id }
          }
          """,
          {"id": connection_id, "shard": shard_id, "state": kind.value},
        )
      else:
        await self._execute(
          """
          mutation ReadyAgain($id: ID!, $state: String!) {
            updateGatewayConnection(id: $id, active: true, state: $state) { id }
          }
          """,
          {"id": connection_id, "state": kind.value},
        )
    elif kind in {
      ConnectionEventKind.DISCONNECTED,
      ConnectionEventKind.RESUMED,
      ConnectionEventKind.CONNECTED,
    }:
      await self._execute(
        """
        mutation State($id: ID!, $active: Boolean!, $state: String!) {
          updateGatewayConnection(id: $id, active: $active, state: $state) { id }
        }
        """,
        {
          "id": connection_id,
          "active": kind is ConnectionEventKind.RESUMED,
          "state": kind.value,
        },
      )
    else:
      await self.purge_connection(connection_id)

  async def purge_connection(self, connection_id: str) -> None:
    result = await self._execute(
      """
      query Owned($id: ID!) {
        gatewayConnection(id: $id) { data { connectionId kind id } }
      }
      """,
      {"id": connection_id},
    )
    connection = result.get("gatewayConnection")
    variables: dict[str, JsonValue] = {"connectionId": connection_id}
    declarations = ["$connectionId: ID!"]
    fields: list[str] = []
    if isinstance(connection, dict) and isinstance(connection.get("data"), list):
      for index, item in enumerate(connection["data"]):
        if isinstance(item, dict):
          kind = item.get("kind")
          object_id = item.get("id")
          if not isinstance(kind, str) or not isinstance(object_id, str):
            continue
          kind_variable = f"kind{index}"
          id_variable = f"id{index}"
          declarations.extend((f"${kind_variable}: String!", f"${id_variable}: ID!"))
          variables[kind_variable] = kind
          variables[id_variable] = object_id
          fields.append(
            f"object{index}: deleteDiscordObject("
            f"connectionId: $connectionId, kind: ${kind_variable}, "
            f"id: ${id_variable})"
          )
    fields.append("connection: deleteGatewayConnection(id: $connectionId)")
    await self._execute(
      f"mutation Purge({', '.join(declarations)}) {{ {' '.join(fields)} }}",
      variables,
    )

  async def _delete_connection(self, request: Request) -> Response:
    await self.purge_connection(request.path_params["connection_id"])
    return Response(status_code=204)

  async def _execute(
    self, query: str, variables: Mapping[str, JsonValue]
  ) -> dict[str, Any]:
    response = await self.store.execute(
      query,
      variables=variables,
      module="micro.gateway.projection",
    )
    if response.get("errors"):
      raise RuntimeError(
        f"Gateway projection store rejected an operation: {response['errors']}"
      )
    data = response.get("data")
    if not isinstance(data, dict):
      raise TypeError("Gateway projection store omitted GraphQL data.")
    return data

  async def _consume(self) -> None:
    await self._topology_ready.wait()
    while True:
      delivery = await self.queue.consume(
        "gateway.projection", "micro-gateway-projection"
      )
      await self._pending.put(delivery)

  async def _project_batches(self) -> None:
    carry: QueueDelivery | None = None
    while True:
      delivery = carry or await self._pending.get()
      carry = None
      try:
        kind = _projection_item_kind(delivery.payload)
      except ValueError:
        await delivery.acknowledge()
        continue
      if kind == "connection":
        try:
          await self.project_connection(delivery.payload)
        except Exception:
          await delivery.retry()
        else:
          await delivery.acknowledge()
        continue
      deliveries = [delivery]
      while len(deliveries) < self._batch_size:
        try:
          following = self._pending.get_nowait()
        except asyncio.QueueEmpty:
          break
        try:
          following_kind = _projection_item_kind(following.payload)
        except ValueError:
          await following.acknowledge()
          continue
        if following_kind == "connection":
          carry = following
          break
        deliveries.append(following)
      try:
        await self.project_events(tuple(delivery.payload for delivery in deliveries))
      except Exception:
        for delivery in deliveries:
          await delivery.retry()
      else:
        for delivery in deliveries:
          await delivery.acknowledge()


def _project_dispatch(
  name: str, payload: dict[str, JsonValue]
) -> tuple[ProjectedObject, ...]:
  deleted = name.endswith("_DELETE") or name in {"GUILD_DELETE", "THREAD_DELETE"}
  guild_id = _string_id(payload.get("guild_id"))
  objects: list[ProjectedObject] = []

  def add(kind: str, value: JsonValue, *, is_deleted: bool = False) -> None:
    if not isinstance(value, dict):
      return
    object_id = _object_id(kind, value)
    if object_id is None:
      return
    object_guild = _string_id(value.get("guild_id")) or guild_id
    objects.append(ProjectedObject(kind, object_id, object_guild, value, is_deleted))

  root_kind = _dispatch_kind(name)
  root = payload.get("role") if root_kind == "role" and "role" in payload else payload
  add(root_kind, root, is_deleted=deleted)
  collections = {
    "guilds": "guild",
    "channels": "channel",
    "threads": "thread",
    "roles": "role",
    "members": "member",
    "emojis": "emoji",
    "voice_states": "voice_state",
    "presences": "presence",
    "stage_instances": "stage_instance",
    "stickers": "sticker",
    "guild_scheduled_events": "scheduled_event",
  }
  for field, kind in collections.items():
    values = payload.get(field)
    if isinstance(values, list):
      for value in values:
        add(kind, value)
  return tuple({(item.kind, item.id): item for item in objects}.values())


def _decode_projection_event(item: bytes) -> tuple[str, str, dict[str, JsonValue]]:
  decoded = from_json(item)
  if (
    not isinstance(decoded, list)
    or len(decoded) != 5
    or decoded[0] != "event"
    or not isinstance(decoded[1], str)
    or isinstance(decoded[2], bool)
    or not isinstance(decoded[2], int)
    or not isinstance(decoded[3], str)
    or not isinstance(decoded[4], dict)
  ):
    raise ValueError(
      "Projection events must be [event, connection_id, shard_id, name, payload]."
    )
  return decoded[1], decoded[3], cast(dict[str, JsonValue], decoded[4])


def _projection_item_kind(item: bytes) -> str:
  decoded = from_json(item)
  if (
    not isinstance(decoded, list)
    or not decoded
    or decoded[0] not in {"event", "connection"}
  ):
    raise ValueError("Projection queue items need an event or connection tag.")
  return cast(str, decoded[0])


def _dispatch_kind(name: str) -> str:
  if name.startswith("GUILD_MEMBER"):
    return "member"
  if name.startswith("GUILD_ROLE"):
    return "role"
  if name.startswith("GUILD_EMOJIS"):
    return "guild"
  return (
    name.removesuffix("_CREATE").removesuffix("_UPDATE").removesuffix("_DELETE").lower()
  )


def _object_id(kind: str, value: Mapping[str, JsonValue]) -> str | None:
  if kind in {"member", "presence"} and isinstance(value.get("user"), dict):
    user = cast(dict[str, JsonValue], value["user"])
    return _string_id(user.get("id"))
  if kind == "voice_state":
    user_id = _string_id(value.get("user_id"))
    guild_id = _string_id(value.get("guild_id"))
    return f"{guild_id}:{user_id}" if guild_id and user_id else user_id
  return _string_id(value.get("id"))


def _string_id(value: JsonValue | None) -> str | None:
  return value if isinstance(value, str) and value else None


def _merge_json(
  current: dict[str, JsonValue], update: dict[str, JsonValue]
) -> dict[str, JsonValue]:
  merged = dict(current)
  for key, value in update.items():
    previous = merged.get(key)
    merged[key] = (
      _merge_json(previous, value)
      if isinstance(previous, dict) and isinstance(value, dict)
      else value
    )
  return merged


__all__ = ("GatewayProjection", "ProjectedObject")
