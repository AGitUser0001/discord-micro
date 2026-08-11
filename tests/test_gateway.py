import asyncio
from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import Any, cast

import hikari
import pytest
from starlette.testclient import TestClient

from micro.gateway import (
  AssignmentState,
  ConnectionEvent,
  ConnectionEventKind,
  Dispatch,
  Gateway,
  GatewayState,
  ShardAssignment,
)


class FakeGatewayBot:
  def __init__(self) -> None:
    self.listeners: dict[type[Any], Callable[[Any], Awaitable[None]]] = {}
    self.start_calls: list[dict[str, Any]] = []
    self.close_calls = 0
    self.presence_updates: list[dict[str, Any]] = []
    self.member_requests: list[tuple[int, dict[str, Any]]] = []
    self.voice_updates: list[tuple[int, int | None, dict[str, Any]]] = []

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

  def update_presence(self, **kwargs: Any) -> None:
    self.presence_updates.append(kwargs)

  def request_guild_members(self, guild: int, **kwargs: Any) -> None:
    self.member_requests.append((guild, kwargs))

  def update_voice_state(self, guild: int, channel: int | None, **kwargs: Any) -> None:
    self.voice_updates.append((guild, channel, kwargs))

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


def test_managed_gateway_rotates_revisioned_credentials() -> None:
  bots: list[FakeGatewayBot] = []
  tokens: list[str] = []

  async def dispatch(event: Dispatch) -> None:
    pass

  gateway = Gateway(intents=hikari.Intents.GUILDS, dispatch=dispatch)

  def create(token: str) -> Any:
    tokens.append(token)
    bot = FakeGatewayBot()
    bots.append(bot)
    return bot

  gateway._new_bot = create  # pyright: ignore[reportPrivateUsage]
  with TestClient(gateway) as client:
    first = client.post("/discord/credential", json={"token": "first", "revision": 0})
    assert client.get("/health/ready").status_code == 204
    rotated = client.post(
      "/discord/credential", json={"token": "second", "revision": 1}
    )
    stale = client.post("/discord/credential", json={"token": "stale", "revision": 0})

  assert first.status_code == 204
  assert rotated.status_code == 204
  assert stale.status_code == 409
  assert tokens == ["first", "second"]
  assert bots[0].close_calls == 1
  assert len(bots[1].start_calls) == 1


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
    ),
    (
      "gateway.projection",
      b'["event",null,0,"MESSAGE_CREATE",{"id":"1","content":"hello"}]',
    ),
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


def test_gateway_requests_complete_members_after_ready() -> None:
  bot = FakeGatewayBot()
  gateway = Gateway(
    "test-token",
    intents=hikari.Intents.GUILDS | hikari.Intents.GUILD_MEMBERS,
    dispatch=lambda event: asyncio.sleep(0),
    shard_ids=[0],
    shard_count=1,
    bot=cast(Any, bot),
  )

  asyncio.run(
    bot.emit(
      hikari.ShardPayloadEvent,
      shard=SimpleNamespace(id=0),
      name="READY",
      payload={"guilds": [{"id": "123"}]},
    )
  )

  assert gateway.shard_ids == (0,)
  assert bot.member_requests[0][0] == 123
  assert bot.member_requests[0][1]["query"] == ""
  assert bot.member_requests[0][1]["limit"] == 0
  assert str(bot.member_requests[0][1]["nonce"]).endswith(":123")


def test_gateway_state_retains_assignment_during_disconnect_and_abandons_death() -> (
  None
):
  state = GatewayState()
  state.set_desired((ShardAssignment("gateway-a", 1, 4),))
  state.observe(
    "gateway-a", ConnectionEvent(ConnectionEventKind.READY, 1, "connection-a")
  )
  assert state.active_shards("gateway-a") == (1,)
  assert state.assignments[0].state is AssignmentState.ACTIVE

  state.observe(
    "gateway-a",
    ConnectionEvent(ConnectionEventKind.DISCONNECTED, 1, "connection-a"),
  )
  assert state.active_shards("gateway-a") == ()
  assert state.assignments[0].state is AssignmentState.ACTIVE

  assert state.declare_dead("gateway-a") == ("connection-a",)
  assert state.assignments[0].state is AssignmentState.ABANDONED


def test_gateway_state_rolls_ownership_only_after_old_assignment_drains() -> None:
  state = GatewayState()
  old = ShardAssignment("gateway-old", 0, 1)
  new = ShardAssignment("gateway-new", 0, 1)
  state.set_desired((old,))
  state.observe(
    "gateway-old", ConnectionEvent(ConnectionEventKind.READY, 0, "connection-old")
  )

  state.set_desired((old, new))
  with pytest.raises(ValueError, match="already has an active"):
    state.observe(
      "gateway-new", ConnectionEvent(ConnectionEventKind.READY, 0, "connection-new")
    )

  state.set_desired((new,))
  state.observe(
    "gateway-new", ConnectionEvent(ConnectionEventKind.READY, 0, "connection-new")
  )
  assert state.active_shards("gateway-old") == ()
  assert state.active_shards("gateway-new") == (0,)
  assert state.active_owner(0, 1) == "gateway-new"


def test_gateway_state_allows_explicit_shard_count_replacement() -> None:
  state = GatewayState()
  state.set_desired((ShardAssignment("old", 0, 1),))
  state.observe("old", ConnectionEvent(ConnectionEventKind.READY, 0, "old-c"))
  state.set_desired((ShardAssignment("new-a", 0, 2), ShardAssignment("new-b", 1, 2)))
  state.observe("new-a", ConnectionEvent(ConnectionEventKind.READY, 0, "new-a-c"))
  state.observe("new-b", ConnectionEvent(ConnectionEventKind.READY, 1, "new-b-c"))

  assert state.active_shards("old") == ()
  assert state.active_owner(0, 2) == "new-a"
  assert state.active_owner(1, 2) == "new-b"


def test_invalid_session_allows_a_fresh_connection_on_the_same_worker() -> None:
  state = GatewayState()
  state.set_desired((ShardAssignment("gateway", 0, 1),))
  state.observe("gateway", ConnectionEvent(ConnectionEventKind.READY, 0, "old"))
  state.observe("gateway", ConnectionEvent(ConnectionEventKind.INVALIDATED, 0, "old"))
  state.observe("gateway", ConnectionEvent(ConnectionEventKind.READY, 0, "new"))

  assert state.active_shards("gateway") == (0,)
  assert state.connections[0].connection_id == "new"


def test_gateway_executes_typed_control_requests() -> None:
  bot = FakeGatewayBot()
  gateway = make_gateway(bot)

  with TestClient(gateway) as client:
    presence = client.post(
      "/gateway/presence",
      json={"status": "idle", "activity": {"name": "Micro", "type": 3}},
    )
    members = client.post(
      "/gateway/guild-members",
      json={"guild_id": 42, "query": "A", "limit": 10, "nonce": "request-1"},
    )
    voice = client.post(
      "/gateway/voice-state",
      json={"guild_id": 42, "channel_id": 99, "self_deaf": True},
    )

  assert presence.status_code == members.status_code == voice.status_code == 204
  assert bot.presence_updates[0]["status"] is hikari.Status.IDLE
  assert bot.presence_updates[0]["activity"].name == "Micro"
  assert bot.member_requests == [
    (
      42,
      {
        "include_presences": False,
        "limit": 10,
        "query": "A",
        "nonce": "request-1",
      },
    )
  ]
  assert bot.voice_updates == [(42, 99, {"self_mute": False, "self_deaf": True})]


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
