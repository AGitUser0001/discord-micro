import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from nats.aio.msg import Msg
from nats.errors import TimeoutError as NatsTimeoutError
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy
from pydantic import JsonValue, ValidationError
from pydantic_core import from_json

from micro import log, subjects
from micro.schemas.gateway import GATEWAY_PROJECTION
from micro.service import Service
from micro.store import StoreClient

from ._events import (
  CONNECTION_HEADER,
  SHARD_HEADER,
  ConnectionEvent,
  ConnectionEventKind,
)

PROJECTION_SUBJECTS = (
  "micro.discord.dispatch.>",
  "micro.discord.standby.>",
  "micro.gateway.connection.>",
)


@dataclass(frozen=True, slots=True)
class ProjectedObject:
  """One object to write to (or delete from) the aggregated state."""

  kind: str
  id: str
  guild_id: str | None
  payload: dict[str, JsonValue]
  deleted: bool = False


class GatewayProjection(Service):
  """Optional service that aggregates what every shard sees into one view of Discord.

  It consumes every connection's dispatches (publishing and standby) plus connection
  lifecycle events, in stream order, and folds them into the store: a guild's roles,
  channels, members and the rest, kept by guild whichever shard or connection delivered
  them. A guild is marked not current while the connection that delivered it has a gap.
  Adjacent dispatches become one atomic mutation. Run one replica: order matters.
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
    self._known: set[str] = set()

  @property
  def store(self) -> StoreClient:
    """The `StoreClient` used to write the aggregated state (raises before start)."""
    if self._store is None:
      raise RuntimeError("Gateway projection has not started.")
    return self._store

  async def on_start(self) -> None:
    """Create the consumer and begin projecting dispatches into the store."""
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
      except asyncio.CancelledError:
        raise
      except Exception:
        # NATS trouble: keep projecting once it is back, do not stop for good.
        log.warning("The projection could not fetch dispatches", exc_info=True)
        await asyncio.sleep(1)
        continue
      async with self.tracked():
        try:
          await self.project_messages(messages)
        except Exception:
          log.exception("Projection batch failed; it will be redelivered")
          for message in messages:
            await message.nak(delay=1)
        else:
          for message in messages:
            await message.ack()

  async def project_messages(self, messages: Sequence[Msg]) -> None:
    """Project stream messages in order, batching adjacent dispatches."""
    pending: list[tuple[str, str, dict[str, JsonValue]]] = []
    shards: dict[str, int] = {}
    for message in messages:
      if message.subject.startswith("micro.gateway.connection."):
        if pending:
          await self._ensure_connections(shards)
          await self.project_events(pending)
          pending = []
        try:
          event = ConnectionEvent.model_validate_json(message.data)
        except ValidationError:
          log.error("Ignoring an invalid connection event")
          continue
        await self.project_connection(event)
        continue
      connection_id = (message.headers or {}).get(CONNECTION_HEADER)
      name = message.subject.split(".")[3]
      try:
        payload = from_json(message.data)
      except ValueError:
        continue  # not JSON: retrying the batch would never get past it
      if connection_id is None or not isinstance(payload, dict):
        continue
      pending.append((connection_id, name, cast(dict[str, JsonValue], payload)))
      shard = (message.headers or {}).get(SHARD_HEADER, "")
      if shard.isdecimal():
        shards[connection_id] = int(shard)
    if pending:
      await self._ensure_connections(shards)
      await self.project_events(pending)

  async def _ensure_connections(self, shards: Mapping[str, int]) -> None:
    """Record connections this projection never saw start.

    A projection started (or restarted) after a connection's READY would
    otherwise have nowhere to attach the guilds that connection delivers.
    """
    for connection_id, shard_id in shards.items():
      if connection_id in self._known:
        continue
      existing = await self._execute(
        "query Connection($id: ID!) { gatewayConnection(id: $id) { id } }",
        {"id": connection_id},
      )
      if existing.get("gatewayConnection") is None:
        await self._execute(
          """
          mutation Adopt($id: ID!, $shard: Int!) {
            createGatewayConnection(id: $id, shardId: $shard) { id }
          }
          """,
          {"id": connection_id, "shard": shard_id},
        )
      self._known.add(connection_id)

  async def project_events(
    self, items: Sequence[tuple[str, str, dict[str, JsonValue]]]
  ) -> None:
    """Fold `(connection_id, dispatch_name, payload)` items into the guilds' state.

    What a guild holds does not depend on which connection delivered it. A
    `GUILD_CREATE` is the guild's whole state: it replaces what was there. Every other
    dispatch changes the objects it names. All of it is one mutation.
    """
    work = _fold(items)
    if not work:
      return
    guild_ids = list(work)

    declarations: list[str] = []
    fields: list[str] = []
    variables: dict[str, JsonValue] = {}
    reads: list[tuple[str, str, str]] = []
    for index, guild_id in enumerate(guild_ids):
      guild = work[guild_id]
      listing = " data { kind id }" if guild.resync or guild.purge else ""
      declarations.append(f"$g{index}: ID!")
      variables[f"g{index}"] = guild_id
      fields.append(
        f"guild{index}: gatewayGuild(id: $g{index}) "
        f"{{ connectionId fresh synced{listing} }}"
      )
      if guild.purge or guild.resync:
        continue  # purged, or replaced whole: nothing to merge with
      for (kind, object_id), projected in guild.objects.items():
        if not projected.deleted:
          reads.append((guild_id, kind, object_id))
    for index, (guild_id, kind, object_id) in enumerate(reads):
      declarations.extend(
        (f"$rg{index}: ID!", f"$rk{index}: String!", f"$ri{index}: ID!")
      )
      variables.update(
        {f"rg{index}": guild_id, f"rk{index}": kind, f"ri{index}": object_id}
      )
      fields.append(
        f"object{index}: discordObject(guildId: $rg{index}, kind: $rk{index}, "
        f"id: $ri{index}) {{ payload }}"
      )
    held = await self._execute(
      f"query State({', '.join(declarations)}) {{ {' '.join(fields)} }}", variables
    )
    current: dict[tuple[str, str, str], dict[str, JsonValue]] = {}
    for index, key in enumerate(reads):
      found = held.get(f"object{index}")
      if isinstance(found, dict) and isinstance(found.get("payload"), dict):
        current[key] = cast(dict[str, JsonValue], found["payload"])

    batch = _Batch()
    for index, guild_id in enumerate(guild_ids):
      guild = work[guild_id]
      state = held.get(f"guild{index}")
      listed = {
        (item["kind"], item["id"])
        for item in (state.get("data") or [] if isinstance(state, dict) else [])
        if isinstance(item, dict)
      }
      if guild.purge:
        for kind, object_id in listed:
          batch.delete(guild_id, kind, object_id)
        batch.add("deleteGatewayGuild", {"id": ("ID!", guild_id)})
        continue
      self._write_guild(
        batch, guild_id, guild, state if isinstance(state, dict) else None
      )
      if guild.resync:
        kept = {key for key, item in guild.objects.items() if not item.deleted}
        for kind, object_id in listed - kept:
          batch.delete(guild_id, kind, object_id)
      for (kind, object_id), projected in guild.objects.items():
        if projected.deleted:
          if not guild.resync:
            batch.delete(guild_id, kind, object_id)
          continue
        if guild.resync:
          exists = (kind, object_id) in listed
          payload = projected.payload
        else:
          before = current.get((guild_id, kind, object_id))
          exists = before is not None
          payload = (
            projected.payload
            if before is None
            else _merge_json(before, projected.payload)
          )
        batch.write(guild_id, kind, object_id, payload, exists=exists)
    if batch.fields:
      await self._execute(batch.mutation(), batch.variables)

  def _write_guild(
    self,
    batch: _Batch,
    guild_id: str,
    guild: _GuildWork,
    state: dict[str, JsonValue] | None,
  ) -> None:
    """Create or update the guild's own row: who delivered it, and whether it is current."""
    if state is None:
      batch.add(
        "createGatewayGuild",
        {
          "id": ("ID!", guild_id),
          "connectionId": ("ID!", guild.connection),
          "fresh": ("Boolean!", not guild.stale),
          "synced": ("Boolean!", guild.resync),
        },
      )
      batch.add(
        "attachGuildToConnection",
        {"connectionId": ("ID!", guild.connection), "guildId": ("ID!", guild_id)},
      )
      return
    connection = str(state["connectionId"])
    fresh = bool(state["fresh"])
    synced = bool(state["synced"])
    if guild.resync:
      if connection != guild.connection:
        connection = guild.connection
        batch.add(
          "attachGuildToConnection",
          {"connectionId": ("ID!", connection), "guildId": ("ID!", guild_id)},
        )
      fresh, synced = True, True
    if guild.stale:
      fresh = False
    if (connection, fresh, synced) != (
      str(state["connectionId"]),
      bool(state["fresh"]),
      bool(state["synced"]),
    ):
      batch.add(
        "updateGatewayGuild",
        {
          "id": ("ID!", guild_id),
          "connectionId": ("ID!", connection),
          "fresh": ("Boolean!", fresh),
          "synced": ("Boolean!", synced),
        },
      )

  async def project_connection(self, event: ConnectionEvent) -> None:
    """Apply a connection lifecycle event to the guilds it delivered.

    A gap (disconnected, or lost for good) makes its guilds not current; a resume,
    which replays what was missed, makes them current again. Nothing is deleted:
    the next `GUILD_CREATE` from a new connection replaces the state in place.
    """
    kind = event.kind
    connection_id = event.connection_id
    if connection_id is None:
      return
    if kind is ConnectionEventKind.READY:
      await self._ensure_connections({connection_id: event.shard_id})
    elif kind is ConnectionEventKind.RESUMED:
      await self._mark_current(connection_id, True)
    elif kind is ConnectionEventKind.DISCONNECTED:
      await self._mark_current(connection_id, False)
    elif kind is not ConnectionEventKind.CONNECTED:
      await self.forget_connection(connection_id)

  async def forget_connection(self, connection_id: str) -> None:
    """A connection is gone for good: its guilds are not current until a new one syncs."""
    self._known.discard(connection_id)
    await self._mark_current(connection_id, False)
    await self._execute(
      "mutation Forget($id: ID!) { gone: deleteGatewayConnection(id: $id) }",
      {"id": connection_id},
    )

  async def _mark_current(self, connection_id: str, fresh: bool) -> None:
    result = await self._execute(
      """
      query Guilds($id: ID!) {
        gatewayConnection(id: $id) { guilds { id connectionId fresh synced } }
      }
      """,
      {"id": connection_id},
    )
    connection = result.get("gatewayConnection")
    if not isinstance(connection, dict):
      return
    batch = _Batch()
    for item in connection.get("guilds") or []:
      if (
        isinstance(item, dict)
        and item.get("connectionId") == connection_id  # not one a newer connection took
        and item.get("fresh") is not fresh
      ):
        batch.add(
          "updateGatewayGuild",
          {
            "id": ("ID!", str(item["id"])),
            "connectionId": ("ID!", connection_id),
            "fresh": ("Boolean!", fresh),
            "synced": ("Boolean!", bool(item["synced"])),
          },
        )
    if batch.fields:
      await self._execute(batch.mutation(), batch.variables)

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


_STATE_KINDS = frozenset(
  (
    "guild",
    "channel",
    "thread",
    "role",
    "member",
    "emoji",
    "voice_state",
    "presence",
    "stage_instance",
    "sticker",
    "scheduled_event",
  )
)
"""What is aggregated: the state of a guild. Messages, typing, reactions and the like are
events, not state, and are not kept."""

_INDEXED = frozenset(("channel", "thread", "role"))
"""Kinds whose ids are unique across Discord, so they can be found without their guild."""


@dataclass(slots=True)
class _GuildWork:
  """What a batch of dispatches does to one guild."""

  connection: str
  objects: dict[tuple[str, str], ProjectedObject] = field(default_factory=dict)
  resync: bool = False
  purge: bool = False
  stale: bool = False


def _fold(
  items: Sequence[tuple[str, str, dict[str, JsonValue]]],
) -> dict[str, _GuildWork]:
  """Group dispatches by guild, in order: a `GUILD_CREATE` starts the guild afresh."""
  work: dict[str, _GuildWork] = {}
  for connection_id, name, payload in items:
    if name == "GUILD_DELETE":
      guild_id = _string_id(payload.get("id"))
      if guild_id is None:
        continue
      guild = work.setdefault(guild_id, _GuildWork(connection_id))
      if payload.get("unavailable") is True:
        guild.stale = True  # an outage, not a removal: keep what is held, not current
      else:
        guild.objects.clear()
        guild.resync, guild.purge = False, True
      continue
    if name == "GUILD_CREATE":
      guild_id = _string_id(payload.get("id"))
      if guild_id is not None:
        guild = work.setdefault(guild_id, _GuildWork(connection_id))
        guild.objects.clear()
        guild.connection = connection_id
        guild.resync, guild.purge, guild.stale = True, False, False
    for projected in _project_dispatch(name, payload):
      if projected.guild_id is None:
        continue  # not about a guild (a DM, a user): there is nowhere to keep it
      guild = work.setdefault(projected.guild_id, _GuildWork(connection_id))
      if guild.purge:
        continue
      key = (projected.kind, projected.id)
      previous = guild.objects.get(key)
      if previous is not None and not previous.deleted and not projected.deleted:
        projected = ProjectedObject(
          projected.kind,
          projected.id,
          projected.guild_id,
          _merge_json(previous.payload, projected.payload),
        )
      guild.objects[key] = projected
  return work


class _Batch:
  """The pieces of one GraphQL mutation, each with variables of its own."""

  def __init__(self) -> None:
    self.declarations: list[str] = []
    self.variables: dict[str, JsonValue] = {}
    self.fields: list[str] = []

  def add(
    self,
    operation: str,
    arguments: Mapping[str, tuple[str, JsonValue]],
    selection: str = "",
  ) -> None:
    index = len(self.fields)
    if (
      not selection
      and operation.startswith(("create", "update"))
      and (operation != "updateDiscordObject")
    ):
      selection = " { id }"  # an operation that returns an entity needs a selection
    passed: list[str] = []
    for name, (graphql_type, value) in arguments.items():
      variable = f"v{index}_{name}"
      self.declarations.append(f"${variable}: {graphql_type}")
      self.variables[variable] = value
      passed.append(f"{name}: ${variable}")
    self.fields.append(f"m{index}: {operation}({', '.join(passed)}){selection}")

  def delete(self, guild_id: str, kind: str, object_id: str) -> None:
    self.add(
      "deleteDiscordObject",
      {
        "guildId": ("ID!", guild_id),
        "kind": ("String!", kind),
        "id": ("ID!", object_id),
      },
    )
    if kind in _INDEXED:
      self.add(
        "deleteDiscordIndex", {"kind": ("String!", kind), "id": ("ID!", object_id)}
      )

  def write(
    self, guild_id: str, kind: str, object_id: str, payload: JsonValue, *, exists: bool
  ) -> None:
    key = {
      "guildId": ("ID!", guild_id),
      "kind": ("String!", kind),
      "id": ("ID!", object_id),
    }
    self.add(
      "updateDiscordObject" if exists else "createDiscordObject",
      {**key, "payload": ("JSON!", payload)},
      " { id }",
    )
    if exists:
      return
    self.add("attachDiscordObject", key)
    if kind == "channel":
      self.add("attachChannel", key)
    elif kind == "role":
      self.add("attachRole", key)
    if kind in _INDEXED:
      self.add(
        "createDiscordIndex",
        {
          "kind": ("String!", kind),
          "id": ("ID!", object_id),
          "guildId": ("ID!", guild_id),
        },
      )

  def mutation(self) -> str:
    return (
      f"mutation Project({', '.join(self.declarations)}) {{ {' '.join(self.fields)} }}"
    )


def _project_dispatch(
  name: str, payload: dict[str, JsonValue]
) -> tuple[ProjectedObject, ...]:
  deleted = name.endswith("_DELETE") or name in {
    "GUILD_DELETE",
    "THREAD_DELETE",
    "GUILD_MEMBER_REMOVE",
  }
  guild_id = _string_id(payload.get("guild_id"))
  if guild_id is None and name in {"GUILD_CREATE", "GUILD_UPDATE"}:
    guild_id = _string_id(payload.get("id"))
  objects: list[ProjectedObject] = []

  def add(kind: str, value: JsonValue, *, is_deleted: bool = False) -> None:
    if not isinstance(value, dict) or kind not in _STATE_KINDS:
      return
    object_guild = _string_id(value.get("guild_id")) or guild_id
    object_id = _object_id(kind, value, object_guild)
    if object_id is None:
      return
    objects.append(ProjectedObject(kind, object_id, object_guild, value, is_deleted))

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
  root_kind = _dispatch_kind(name)
  root = payload.get("role") if root_kind == "role" and "role" in payload else payload
  if name == "GUILD_ROLE_DELETE":
    root = {"id": payload.get("role_id"), "guild_id": payload.get("guild_id")}
  if root_kind == "guild" and isinstance(root, dict):
    # The lists are objects of their own, kept current one by one; left in the guild
    # they would only go stale.
    root = {key: value for key, value in root.items() if key not in collections}
  add(root_kind, root, is_deleted=deleted)
  for collection, kind in collections.items():
    values = payload.get(collection)
    if isinstance(values, list):
      for value in values:
        add(kind, value)
  return tuple({(item.kind, item.id): item for item in objects}.values())


def _dispatch_kind(name: str) -> str:
  if name.startswith("GUILD_MEMBER"):
    return "member"
  if name.startswith("GUILD_ROLE"):
    return "role"
  if name.startswith("GUILD_SCHEDULED_EVENT"):
    return "scheduled_event"
  if name.startswith("GUILD_EMOJIS"):
    return "guild"
  return (
    name.removesuffix("_CREATE").removesuffix("_UPDATE").removesuffix("_DELETE").lower()
  )


def _object_id(
  kind: str, value: Mapping[str, JsonValue], guild_id: str | None = None
) -> str | None:
  if kind in {"member", "presence"} and isinstance(value.get("user"), dict):
    # A user is a different member in every guild, so the id carries the guild.
    user = cast(dict[str, JsonValue], value["user"])
    user_id = _string_id(user.get("id"))
    return f"{guild_id}:{user_id}" if guild_id and user_id else user_id
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
