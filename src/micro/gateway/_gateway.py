import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid7

import hikari
from starlette.types import Receive, Scope, Send

from micro.service import Service

from ._runner import event_loop_factory


@dataclass(frozen=True, slots=True)
class Dispatch:
  name: str
  shard_id: int
  sequence: int
  connection_id: str | None
  payload: Mapping[str, Any]


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


async def _ignore_connection_event(event: ConnectionEvent) -> None:
  pass


class Gateway:
  def __init__(
    self,
    token: str,
    *,
    intents: hikari.Intents,
    dispatch: DispatchSink,
    connection: ConnectionSink = _ignore_connection_event,
    shard_ids: Sequence[int] | None = None,
    shard_count: int | None = None,
    bot: _GatewayBot | None = None,
  ) -> None:
    if not token:
      raise ValueError("token cannot be empty.")
    self._shard_ids, self._shard_count = _validate_shards(shard_ids, shard_count)
    self._dispatch_sink = dispatch
    self._connection_sink = connection
    self._sequences: dict[int, int] = {}
    self._connections: dict[int, str] = {}
    self._started = False
    self._service = Service("micro.gateway")
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

  @property
  def service(self) -> Service:
    return self._service

  @property
  def shard_ids(self) -> tuple[int, ...] | None:
    return self._shard_ids

  @property
  def shard_count(self) -> int | None:
    return self._shard_count

  def dynamic_schema(self, *, root_path: str = "") -> dict[str, Any]:
    return self._service.dynamic_schema(root_path=root_path)

  def run(self) -> None:
    """Run the Gateway until it closes, using an accelerated loop if available."""
    try:
      with asyncio.Runner(loop_factory=event_loop_factory) as runner:
        runner.run(self._run_until_closed())
    except KeyboardInterrupt:
      pass

  async def start(self) -> None:
    if self._started:
      raise RuntimeError("Gateway is already running.")
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
    if not self._started:
      return
    try:
      await self._bot.close()
    finally:
      connections, self._connections = self._connections, {}
      for shard_id, connection_id in connections.items():
        await self._connection_sink(
          ConnectionEvent(ConnectionEventKind.CLOSED, shard_id, connection_id)
        )
      self._started = False

  async def _run_until_closed(self) -> None:
    try:
      await self.start()
      await self._bot.join()
    finally:
      await self.close()

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "lifespan":
      await self._service(scope, receive, send)
      return
    await self._lifespan(receive, send)

  def _subscribe(self) -> None:
    self._bot.listen(hikari.ShardPayloadEvent)(self._on_dispatch)
    self._bot.listen(hikari.ShardConnectedEvent)(self._on_connected)
    self._bot.listen(hikari.ShardDisconnectedEvent)(self._on_disconnected)

  async def _on_dispatch(self, event: hikari.ShardPayloadEvent) -> None:
    shard_id = event.shard.id
    if event.name == "READY":
      await self._on_ready(shard_id)
    elif event.name == "RESUMED":
      await self._on_resumed(shard_id)

    sequence = self._sequences.get(shard_id, 0) + 1
    self._sequences[shard_id] = sequence
    await self._dispatch_sink(
      Dispatch(
        name=event.name,
        shard_id=shard_id,
        sequence=sequence,
        connection_id=self._connections.get(shard_id),
        payload=event.payload,
      )
    )

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

  async def _on_ready(self, shard_id: int) -> None:
    if previous := self._connections.get(shard_id):
      await self._connection_sink(
        ConnectionEvent(ConnectionEventKind.INVALIDATED, shard_id, previous)
      )
    connection_id = str(uuid7())
    self._connections[shard_id] = connection_id
    self._sequences[shard_id] = 0
    await self._connection_sink(
      ConnectionEvent(ConnectionEventKind.READY, shard_id, connection_id)
    )

  async def _on_resumed(self, shard_id: int) -> None:
    await self._connection_sink(
      ConnectionEvent(
        ConnectionEventKind.RESUMED,
        shard_id,
        self._connections.get(shard_id),
      )
    )

  async def _lifespan(self, receive: Receive, send: Send) -> None:
    while True:
      message = await receive()
      if message["type"] == "lifespan.startup":
        try:
          await self.start()
        except BaseException as exc:
          await send({"type": "lifespan.startup.failed", "message": str(exc)})
          return
        await send({"type": "lifespan.startup.complete"})
      elif message["type"] == "lifespan.shutdown":
        try:
          await self.close()
        except BaseException as exc:
          await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
          return
        await send({"type": "lifespan.shutdown.complete"})
        return


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
