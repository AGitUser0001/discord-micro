import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from nats.aio.msg import Msg
from nats.errors import TimeoutError as NatsTimeoutError
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from pydantic import JsonValue, ValidationError
from pydantic_core import from_json

from micro import subjects
from micro.schemas.gateway import GATEWAY_PROJECTION
from micro.service import Service
from micro.store import StoreClient

from ._events import CONNECTION_HEADER, ConnectionEvent, ConnectionEventKind

logger = logging.getLogger("micro")

PROJECTION_SUBJECTS = (
  "micro.discord.dispatch.>",
  "micro.discord.standby.>",
  "micro.gateway.connection.>",
)


@dataclass(frozen=True, slots=True)
class ProjectedObject:
  kind: str
  id: str
  guild_id: str | None
  payload: dict[str, JsonValue]
  deleted: bool = False


class GatewayProjection(Service):
  """Optional service keeping connection-owned Discord state in the store.

  It consumes every connection's dispatches (publishing and standby) plus
  connection lifecycle events, in stream order, and batches adjacent dispatches
  into one atomic mutation. Run one replica: projection order matters.
  """

  def __init__(
    self, *, name: str = "gateway.projection", batch_size: int = 100
  ) -> None:
    if not 1 <= batch_size <= 1000:
      raise ValueError("batch_size must be between 1 and 1000.")
    super().__init__(name)
    self.uses(GATEWAY_PROJECTION)
    self._batch_size = batch_size
    self._store: StoreClient | None = None

  @property
  def store(self) -> StoreClient:
    if self._store is None:
      raise RuntimeError("Gateway projection has not started.")
    return self._store

  async def on_start(self) -> None:
    await super().on_start()
    self._store = StoreClient(self.client)
    js = self.runtime.jetstream
    durable = subjects.durable("svc", self.name)
    await js.add_consumer(
      subjects.EVENTS_STREAM,
      ConsumerConfig(
        durable_name=durable,
        ack_policy=AckPolicy.EXPLICIT,
        deliver_policy=DeliverPolicy.NEW,
        filter_subjects=list(PROJECTION_SUBJECTS),
        max_ack_pending=-1,
        max_deliver=-1,
      ),
    )
    subscription = await js.pull_subscribe_bind(durable, subjects.EVENTS_STREAM)
    self.spawn(self._consume(subscription), name="project")

  async def _consume(self, subscription: Any) -> None:
    while self.active:
      try:
        messages: list[Msg] = await subscription.fetch(self._batch_size, timeout=5)
      except NatsTimeoutError:
        continue
      async with self.tracked():
        try:
          await self.project_messages(messages)
        except Exception:
          logger.exception("Projection batch failed; it will be redelivered")
          for message in messages:
            await message.nak(delay=1)
        else:
          for message in messages:
            await message.ack()

  async def project_messages(self, messages: Sequence[Msg]) -> None:
    """Project stream messages in order, batching adjacent dispatches."""
    pending: list[tuple[str, str, dict[str, JsonValue]]] = []
    for message in messages:
      if message.subject.startswith("micro.gateway.connection."):
        if pending:
          await self.project_events(pending)
          pending = []
        try:
          event = ConnectionEvent.model_validate_json(message.data)
        except ValidationError:
          logger.error("Ignoring an invalid connection event")
          continue
        await self.project_connection(event)
        continue
      connection_id = (message.headers or {}).get(CONNECTION_HEADER)
      name = message.subject.split(".")[3]
      payload = from_json(message.data)
      if connection_id is None or not isinstance(payload, dict):
        continue
      pending.append((connection_id, name, cast(dict[str, JsonValue], payload)))
    if pending:
      await self.project_events(pending)

  async def project_events(
    self, items: Sequence[tuple[str, str, dict[str, JsonValue]]]
  ) -> None:
    """Project `(connection_id, dispatch_name, payload)` items as one mutation."""
    projected_by_key: dict[tuple[str, str, str], ProjectedObject] = {}
    for connection_id, name, payload in items:
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

  async def project_connection(self, event: ConnectionEvent) -> None:
    kind = event.kind
    shard_id = event.shard_id
    connection_id = event.connection_id
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

  async def _execute(
    self, query: str, variables: Mapping[str, JsonValue]
  ) -> dict[str, Any]:
    response = await self.store.execute(query, variables=dict(variables))
    if response.get("errors"):
      raise RuntimeError(
        f"Gateway projection store rejected an operation: {response['errors']}"
      )
    data = response.get("data")
    if not isinstance(data, dict):
      raise TypeError("Gateway projection store omitted GraphQL data.")
    return data


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
