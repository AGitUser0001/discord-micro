import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid7

import hikari
from pydantic import JsonValue
from pydantic_core import to_json

from micro._microservices import Microservice
from micro.queue import QueueClient

from ._runner import event_loop_factory


@dataclass(frozen=True, slots=True)
class Dispatch:
  name: str
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


class Gateway(Microservice):
  def __init__(
    self,
    token: str,
    *,
    intents: hikari.Intents,
    dispatch: DispatchSink | None = None,
    connection: ConnectionSink = _ignore_connection_event,
    shard_ids: Sequence[int] | None = None,
    shard_count: int | None = None,
    bot: _GatewayBot | None = None,
  ) -> None:
    if not token:
      raise ValueError("token cannot be empty.")
    self.queue = QueueClient()
    super().__init__("gateway", state_receiver=self)
    self._shard_ids, self._shard_count = _validate_shards(shard_ids, shard_count)
    self._uses_queue_dispatch = dispatch is None
    self._dispatch_sink = dispatch or self._publish_dispatch
    self._connection_sink = connection
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
    return document

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
      await self._on_ready(shard_id)
    elif event.name == "RESUMED":
      await self._on_resumed(shard_id)

    await self._dispatch_sink(
      Dispatch(
        name=event.name,
        payload=event.payload,
      )
    )

  async def _publish_dispatch(self, dispatch: Dispatch) -> None:
    await self.queue.publish(
      "gateway.events",
      to_json((dispatch.name, dispatch.payload)),
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
