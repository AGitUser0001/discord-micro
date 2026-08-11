import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid7

import hikari
from pydantic import BaseModel, JsonValue, ValidationError
from pydantic_core import to_json
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from micro._microservices import (
  GuildMembersRequest,
  Microservice,
  PresenceUpdate,
  VoiceStateUpdate,
  request_content_type,
)
from micro.queue import QueueClient

from ._runner import event_loop_factory


@dataclass(frozen=True, slots=True)
class Dispatch:
  name: str
  payload: Mapping[str, Any]
  shard_id: int = 0
  connection_id: str | None = None


class ConnectionEventKind(StrEnum):
  CONNECTED = "connected"
  DISCONNECTED = "disconnected"
  READY = "ready"
  RESUMED = "resumed"
  INVALIDATED = "invalidated"
  CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ConnectionEvent:
  kind: ConnectionEventKind
  shard_id: int
  connection_id: str | None = None


type DispatchSink = Callable[[Dispatch], Awaitable[None]]
type ConnectionSink = Callable[[ConnectionEvent], Awaitable[None]]


class _GatewayBot(Protocol):
  def listen[EventT: hikari.Event](
    self, *event_types: type[EventT]
  ) -> Callable[
    [Callable[[EventT], Awaitable[None]]], Callable[[EventT], Awaitable[None]]
  ]: ...

  async def start(
    self,
    *,
    check_for_updates: bool = True,
    shard_ids: Sequence[int] | None = None,
    shard_count: int | None = None,
  ) -> None: ...

  async def close(self) -> None: ...

  async def join(self) -> None: ...

  def update_presence(self, **kwargs: Any) -> None: ...

  def request_guild_members(self, guild: int, **kwargs: Any) -> None: ...

  def update_voice_state(
    self, guild: int, channel: int | None, **kwargs: Any
  ) -> None: ...


class Gateway(Microservice):
  def __init__(
    self,
    token: str,
    *,
    intents: hikari.Intents,
    dispatch: DispatchSink | None = None,
    connection: ConnectionSink | None = None,
    shard_ids: Sequence[int] | None = None,
    shard_count: int | None = None,
    bot: _GatewayBot | None = None,
  ) -> None:
    if not token:
      raise ValueError("token cannot be empty.")
    self.queue = QueueClient()
    super().__init__("gateway")
    self._intents = intents
    self._shard_ids, self._shard_count = _validate_shards(shard_ids, shard_count)
    self._uses_queue_dispatch = dispatch is None
    self._dispatch_sink = dispatch or self._publish_dispatch
    self._external_connection_sink = connection
    self._connection_sink = self._report_connection
    self._connections: dict[int, str] = {}
    self._started = False
    self._topology_ready = asyncio.Event()
    self._activation: asyncio.Task[None] | None = None
    self._bot = bot or hikari.GatewayBot(
      token,
      intents=intents,
      cache_settings=hikari.impl.CacheSettings(
        components=hikari.api.CacheComponents.NONE
      ),
      auto_chunk_members=False,
      banner=None,
    )
    self._subscribe()
    self.add_route(
      "/gateway/presence",
      self._update_presence,
      methods=("POST",),
      name="gateway:presence",
    )
    self.add_route(
      "/gateway/guild-members",
      self._request_guild_members,
      methods=("POST",),
      name="gateway:guild-members",
    )
    self.add_route(
      "/gateway/voice-state",
      self._update_voice_state,
      methods=("POST",),
      name="gateway:voice-state",
    )

  @property
  def service(self) -> Microservice:
    return self

  @property
  def shard_ids(self) -> tuple[int, ...] | None:
    return self._shard_ids

  @property
  def shard_count(self) -> int | None:
    return self._shard_count

  @property
  def component_ready(self) -> bool:
    return self._started

  def apply_state(self, state: JsonValue) -> None:
    self.queue.apply_state(state)
    self._topology_ready.set()

  def schema_document(self, root_path: str) -> dict[str, JsonValue]:
    document = super().schema_document(root_path)
    document["service"] = "micro.gateway"
    document["events"] = []
    document["requests"] = []
    document["shard_ids"] = list(self._shard_ids or ())
    document["shard_count"] = self._shard_count
    return document

  async def _update_presence(self, request: Request) -> Response:
    update = await _control_request(request, PresenceUpdate)
    if isinstance(update, Response):
      return update
    activity = (
      hikari.Activity(
        name=update.activity.name,
        type=hikari.ActivityType(update.activity.type),
        url=update.activity.url,
        state=update.activity.state,
      )
      if update.activity is not None
      else None
    )
    self._bot.update_presence(
      status=hikari.Status(update.status),
      idle_since=update.idle_since,
      activity=activity,
      afk=update.afk,
    )
    return Response(status_code=204)

  async def _request_guild_members(self, request: Request) -> Response:
    members = await _control_request(request, GuildMembersRequest)
    if isinstance(members, Response):
      return members
    kwargs: dict[str, Any] = {
      "include_presences": members.include_presences,
      "limit": members.limit,
    }
    if members.query is not None:
      kwargs["query"] = members.query
    if members.users is not None:
      kwargs["users"] = members.users
    if members.nonce is not None:
      kwargs["nonce"] = members.nonce
    self._bot.request_guild_members(members.guild_id, **kwargs)
    return Response(status_code=204)

  async def _update_voice_state(self, request: Request) -> Response:
    update = await _control_request(request, VoiceStateUpdate)
    if isinstance(update, Response):
      return update
    self._bot.update_voice_state(
      update.guild_id,
      update.channel_id,
      self_mute=update.self_mute,
      self_deaf=update.self_deaf,
    )
    return Response(status_code=204)

  def run(self) -> None:
    """Run the Gateway until it closes, using an accelerated loop if available."""
    try:
      with asyncio.Runner(loop_factory=event_loop_factory) as runner:
        runner.run(self._run_until_closed())
    except KeyboardInterrupt:
      pass

  async def start(self) -> None:
    if self._started or self._activation is not None:
      raise RuntimeError("Gateway is already running.")
    if self._uses_queue_dispatch:
      self._activation = asyncio.create_task(
        self._activate(), name="micro.gateway.activate"
      )
      return
    await self._start_bot()

  async def _activate(self) -> None:
    await self._topology_ready.wait()
    await self._start_bot()

  async def _start_bot(self) -> None:
    self._started = True
    try:
      await self._bot.start(
        check_for_updates=False,
        shard_ids=self._shard_ids,
        shard_count=self._shard_count,
      )
    except BaseException:
      self._started = False
      raise

  async def close(self) -> None:
    if self._activation is not None:
      if not self._activation.done():
        self._activation.cancel()
      await asyncio.gather(self._activation, return_exceptions=True)
      self._activation = None
    try:
      if self._started:
        await self._bot.close()
    finally:
      connections, self._connections = self._connections, {}
      for shard_id, connection_id in connections.items():
        await self._connection_sink(
          ConnectionEvent(ConnectionEventKind.CLOSED, shard_id, connection_id)
        )
      self._started = False
      await self.queue.aclose()

  async def _run_until_closed(self) -> None:
    try:
      await self.start()
      if self._activation is not None:
        await self._activation
      await self._bot.join()
    finally:
      await self.close()

  def _subscribe(self) -> None:
    self._bot.listen(hikari.ShardPayloadEvent)(self._on_dispatch)
    self._bot.listen(hikari.ShardConnectedEvent)(self._on_connected)
    self._bot.listen(hikari.ShardDisconnectedEvent)(self._on_disconnected)

  async def _on_dispatch(self, event: hikari.ShardPayloadEvent) -> None:
    shard_id = event.shard.id
    if event.name == "READY":
      await self._on_ready(shard_id, event.payload)
    elif event.name == "RESUMED":
      await self._on_resumed(shard_id)

    await self._dispatch_sink(
      Dispatch(
        name=event.name,
        payload=event.payload,
        shard_id=shard_id,
        connection_id=self._connections.get(shard_id),
      )
    )

  async def _publish_dispatch(self, dispatch: Dispatch) -> None:
    await self.queue.publish(
      "gateway.events",
      to_json((dispatch.name, dispatch.payload)),
    )
    await self.queue.publish(
      "gateway.projection",
      to_json(
        (
          "event",
          dispatch.connection_id,
          dispatch.shard_id,
          dispatch.name,
          dispatch.payload,
        )
      ),
    )

  async def _publish_connection(self, event: ConnectionEvent) -> None:
    await self.queue.publish(
      "gateway.projection",
      to_json(("connection", event.kind, event.shard_id, event.connection_id)),
    )

  async def _report_connection(self, event: ConnectionEvent) -> None:
    if self._uses_queue_dispatch:
      await self._publish_connection(event)
    if self._external_connection_sink is not None:
      await self._external_connection_sink(event)

  async def _on_connected(self, event: hikari.ShardConnectedEvent) -> None:
    await self._connection_sink(
      ConnectionEvent(
        ConnectionEventKind.CONNECTED,
        event.shard.id,
        self._connections.get(event.shard.id),
      )
    )

  async def _on_disconnected(self, event: hikari.ShardDisconnectedEvent) -> None:
    await self._connection_sink(
      ConnectionEvent(
        ConnectionEventKind.DISCONNECTED,
        event.shard.id,
        self._connections.get(event.shard.id),
      )
    )

  async def _on_ready(self, shard_id: int, payload: Mapping[str, Any]) -> None:
    if previous := self._connections.get(shard_id):
      await self._connection_sink(
        ConnectionEvent(ConnectionEventKind.INVALIDATED, shard_id, previous)
      )
    connection_id = str(uuid7())
    self._connections[shard_id] = connection_id
    await self._connection_sink(
      ConnectionEvent(ConnectionEventKind.READY, shard_id, connection_id)
    )
    if self._intents & hikari.Intents.GUILD_MEMBERS:
      guilds = payload.get("guilds")
      if isinstance(guilds, list):
        for guild in guilds:
          if not isinstance(guild, Mapping):
            continue
          guild_id = guild.get("id")
          if isinstance(guild_id, str) and guild_id.isdecimal():
            self._bot.request_guild_members(
              int(guild_id),
              include_presences=bool(self._intents & hikari.Intents.GUILD_PRESENCES),
              query="",
              limit=0,
              nonce=f"micro:{connection_id}:{guild_id}",
            )

  async def _on_resumed(self, shard_id: int) -> None:
    await self._connection_sink(
      ConnectionEvent(
        ConnectionEventKind.RESUMED,
        shard_id,
        self._connections.get(shard_id),
      )
    )


def _validate_shards(
  shard_ids: Sequence[int] | None,
  shard_count: int | None,
) -> tuple[tuple[int, ...] | None, int | None]:
  if shard_count is not None and (
    isinstance(shard_count, bool)
    or not isinstance(shard_count, int)
    or not 1 <= shard_count <= 4096
  ):
    raise ValueError("shard_count must be between 1 and 4096.")
  if shard_ids is None:
    return None, shard_count
  if shard_count is None:
    raise ValueError("shard_count is required when shard_ids are specified.")

  normalized = tuple(dict.fromkeys(shard_ids))
  if any(
    isinstance(shard_id, bool)
    or not isinstance(shard_id, int)
    or not 0 <= shard_id < shard_count
    for shard_id in normalized
  ):
    raise ValueError("Every shard ID must be between 0 and shard_count - 1.")
  if not normalized:
    raise ValueError("shard_ids cannot be empty.")
  return normalized, shard_count


async def _control_request[ModelT: BaseModel](
  request: Request,
  model: type[ModelT],
) -> ModelT | Response:
  if request_content_type(request) != "application/json":
    return JSONResponse(
      {"detail": "Gateway control requests require application/json."},
      status_code=415,
    )
  try:
    return model.model_validate_json(await request.body())
  except ValidationError as exc:
    return JSONResponse(
      {
        "detail": "Gateway control request does not match its schema.",
        "errors": exc.errors(include_url=False),
      },
      status_code=422,
    )
