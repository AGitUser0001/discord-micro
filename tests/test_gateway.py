import asyncio
from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import Any, cast

import hikari
import pytest
from starlette.testclient import TestClient

from micro.gateway import ConnectionEvent, ConnectionEventKind, Dispatch, Gateway


class FakeGatewayBot:
  def __init__(self) -> None:
    self.listeners: dict[type[Any], Callable[[Any], Awaitable[None]]] = {}
    self.start_calls: list[dict[str, Any]] = []
    self.close_calls = 0

  def listen(self, *event_types: type[Any]) -> Any:
    def register(callback: Callable[[Any], Awaitable[None]]) -> Any:
      for event_type in event_types:
        self.listeners[event_type] = callback
      return callback

    return register

  async def start(self, **kwargs: Any) -> None:
    self.start_calls.append(kwargs)

  async def close(self) -> None:
    self.close_calls += 1

  async def join(self) -> None:
    pass

  async def emit(self, event_type: type[Any], **values: Any) -> None:
    await self.listeners[event_type](SimpleNamespace(**values))


def make_gateway(
  bot: FakeGatewayBot,
  dispatches: list[Dispatch] | None = None,
  connections: list[ConnectionEvent] | None = None,
) -> Gateway:
  dispatches = dispatches if dispatches is not None else []
  connections = connections if connections is not None else []

  async def dispatch(event: Dispatch) -> None:
    dispatches.append(event)

  async def connection(event: ConnectionEvent) -> None:
    connections.append(event)

  return Gateway(
    "test-token",
    intents=hikari.Intents.GUILDS,
    dispatch=dispatch,
    connection=connection,
    shard_ids=[1, 3],
    shard_count=4,
    bot=cast(Any, bot),
  )


def test_gateway_lifespan_starts_assigned_shards_and_closes() -> None:
  bot = FakeGatewayBot()
  gateway = make_gateway(bot)

  with TestClient(gateway) as client:
    assert client.get("/health/live").status_code == 204
    schema = client.get("/schema").json()

  assert schema["service"] == "micro.gateway"
  assert bot.start_calls == [
    {
      "check_for_updates": False,
      "shard_ids": (1, 3),
      "shard_count": 4,
    }
  ]
  assert bot.close_calls == 1


def test_gateway_run_owns_the_event_loop_and_lifecycle() -> None:
  bot = FakeGatewayBot()
  gateway = make_gateway(bot)

  gateway.run()

  assert len(bot.start_calls) == 1
  assert bot.close_calls == 1


def test_gateway_forwards_raw_dispatches() -> None:
  bot = FakeGatewayBot()
  dispatches: list[Dispatch] = []
  gateway = make_gateway(bot, dispatches=dispatches)
  shard = SimpleNamespace(id=3)

  async def exercise() -> None:
    await bot.emit(
      hikari.ShardPayloadEvent,
      name="MESSAGE_CREATE",
      payload={"id": "1", "content": "first"},
      shard=shard,
    )
    await bot.emit(
      hikari.ShardPayloadEvent,
      name="MESSAGE_UPDATE",
      payload={"id": "1", "content": "second"},
      shard=shard,
    )

  asyncio.run(exercise())

  assert [event.name for event in dispatches] == [
    "MESSAGE_CREATE",
    "MESSAGE_UPDATE",
  ]
  assert dispatches[0].payload == {"id": "1", "content": "first"}
  assert gateway.shard_ids == (1, 3)


def test_gateway_publishes_compact_dispatches_to_one_queue_channel() -> None:
  bot = FakeGatewayBot()
  gateway = Gateway(
    "test-token",
    intents=hikari.Intents.GUILDS,
    bot=cast(Any, bot),
  )
  publications: list[tuple[str, bytes]] = []

  async def publish(channel: str, payload: bytes) -> None:
    publications.append((channel, payload))

  gateway.queue.publish = publish  # type: ignore[method-assign]

  asyncio.run(
    bot.emit(
      hikari.ShardPayloadEvent,
      name="MESSAGE_CREATE",
      payload={"id": "1", "content": "hello"},
      shard=SimpleNamespace(id=0),
    )
  )

  assert publications == [
    (
      "gateway.events",
      b'["MESSAGE_CREATE",{"id":"1","content":"hello"}]',
    )
  ]


def test_queue_backed_gateway_waits_for_queue_topology_before_connecting() -> None:
  bot = FakeGatewayBot()
  gateway = Gateway(
    "test-token",
    intents=hikari.Intents.GUILDS,
    bot=cast(Any, bot),
  )

  async def exercise() -> None:
    await gateway.start()
    assert bot.start_calls == []
    gateway.apply_state(
      {
        "revision": 0,
        "queues": [{"id": "queue-1", "base_url": "http://queue.internal"}],
      }
    )
    activation = cast(Any, gateway)._activation
    assert activation is not None
    await activation
    await gateway.close()

  asyncio.run(exercise())
  assert len(bot.start_calls) == 1
  assert bot.close_calls == 1


def test_gateway_reports_connection_lifecycle() -> None:
  bot = FakeGatewayBot()
  connections: list[ConnectionEvent] = []
  make_gateway(bot, connections=connections)
  shard = SimpleNamespace(id=1)

  async def exercise() -> None:
    await bot.emit(hikari.ShardConnectedEvent, shard=shard)
    await bot.emit(
      hikari.ShardPayloadEvent,
      shard=shard,
      name="READY",
      payload={},
    )
    await bot.emit(hikari.ShardDisconnectedEvent, shard=shard)
    await bot.emit(
      hikari.ShardPayloadEvent,
      shard=shard,
      name="RESUMED",
      payload={},
    )

  asyncio.run(exercise())

  assert connections[0] == ConnectionEvent(ConnectionEventKind.CONNECTED, 1)
  connection_id = connections[1].connection_id
  assert connection_id is not None
  assert connections[1:] == [
    ConnectionEvent(ConnectionEventKind.READY, 1, connection_id),
    ConnectionEvent(ConnectionEventKind.DISCONNECTED, 1, connection_id),
    ConnectionEvent(ConnectionEventKind.RESUMED, 1, connection_id),
  ]


def test_new_ready_invalidates_the_previous_connection() -> None:
  bot = FakeGatewayBot()
  connections: list[ConnectionEvent] = []
  make_gateway(bot, connections=connections)
  shard = SimpleNamespace(id=1)

  async def exercise() -> None:
    await bot.emit(hikari.ShardPayloadEvent, shard=shard, name="READY", payload={})
    await bot.emit(hikari.ShardPayloadEvent, shard=shard, name="READY", payload={})

  asyncio.run(exercise())

  first_id = connections[0].connection_id
  second_id = connections[2].connection_id
  assert first_id is not None
  assert second_id is not None
  assert first_id != second_id
  assert connections == [
    ConnectionEvent(ConnectionEventKind.READY, 1, first_id),
    ConnectionEvent(ConnectionEventKind.INVALIDATED, 1, first_id),
    ConnectionEvent(ConnectionEventKind.READY, 1, second_id),
  ]


@pytest.mark.parametrize(
  ("shard_ids", "shard_count"),
  [([0], None), ([], 1), ([1], 1), ([True], 2), (None, 0)],
)
def test_gateway_rejects_invalid_shard_assignments(
  shard_ids: list[int] | None,
  shard_count: int | None,
) -> None:
  async def dispatch(event: Dispatch) -> None:
    pass

  with pytest.raises(ValueError):
    Gateway(
      "test-token",
      intents=hikari.Intents.NONE,
      dispatch=dispatch,
      shard_ids=shard_ids,
      shard_count=shard_count,
      bot=cast(Any, FakeGatewayBot()),
    )
