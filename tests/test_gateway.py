import asyncio
import json
from collections.abc import Callable, Mapping
from typing import Any

import pytest

from micro import subjects
from micro.gateway import (
  ConnectionEventKind,
  GatewayControl,
  GatewayWorker,
  GuildMembersRequest,
  PresenceUpdate,
  ShardHost,
  VoiceStateUpdate,
  guild_of,
)
from micro.runtime import Runtime

SESSIONS: list[FakeShard] = []


class FakeShard:
  def __init__(self, host: ShardHost, generation: int, shard_id: int, shard_count: int) -> None:
    self.host = host
    self.generation = generation
    self.shard_id = shard_id
    self.shard_count = shard_count
    self.connection_id: str | None = None
    self.started = False
    self.closed = False
    self.presence: list[PresenceUpdate] = []
    self.members: list[GuildMembersRequest] = []
    self.voice: list[VoiceStateUpdate] = []
    SESSIONS.append(self)

  async def start(self) -> None:
    self.started = True
    self.connection_id = f"{self.generation}.{self.shard_id}.{id(self)}"
    await self.host.on_connection(self, ConnectionEventKind.READY)

  async def close(self) -> None:
    self.closed = True

  async def update_presence(self, update: PresenceUpdate) -> None:
    self.presence.append(update)

  async def request_guild_members(self, request: GuildMembersRequest) -> None:
    self.members.append(request)

  async def update_voice_state(self, update: VoiceStateUpdate) -> None:
    self.voice.append(update)

  async def dispatch(self, name: str, payload: Mapping[str, Any]) -> None:
    await self.host.on_dispatch(self, name, payload)


@pytest.fixture(autouse=True)
def _reset() -> None:
  SESSIONS.clear()


def worker(shards: int = 1) -> GatewayWorker:
  return GatewayWorker(
    "token",
    intents=0,
    shard_count=shards,
    lease_ttl=3,
    max_concurrency=16,
    session_factory=FakeShard,
  )


async def eventually(predicate: Callable[[], bool], timeout: float = 20.0) -> None:
  deadline = asyncio.get_running_loop().time() + timeout
  while not predicate():
    if asyncio.get_running_loop().time() > deadline:
      raise AssertionError("condition was not met in time")
    await asyncio.sleep(0.05)


def live(generation: int | None = None) -> list[FakeShard]:
  return [
    s for s in SESSIONS
    if s.started and not s.closed and (generation is None or s.generation == generation)
  ]


def test_single_worker_owns_every_shard_and_publishes(nats_url: str) -> None:
  async def exercise() -> None:
    gateway = worker(shards=2)
    async with Runtime(nats_url) as runtime:
      received: list[tuple[str, dict[str, Any]]] = []

      async def collect(message: Any) -> None:
        received.append((message.subject, dict(message.headers or {})))

      await runtime.nats.subscribe("micro.discord.>", cb=collect)
      await runtime.add(gateway)
      await eventually(lambda: gateway.publishing_shards == (0, 1))
      session = next(s for s in live() if s.shard_id == 1)
      await session.dispatch("MESSAGE_CREATE", {"guild_id": "123", "id": "9"})
      await eventually(lambda: bool(received))
      subject, headers = received[0]
      assert subject == subjects.dispatch("MESSAGE_CREATE", 123)
      assert headers["Micro-Shard"] == "1"

  asyncio.run(exercise())


def test_workers_balance_and_reclaim_a_crashed_worker(nats_url: str) -> None:
  async def exercise() -> None:
    first, second = worker(shards=4), worker(shards=4)
    a, b = Runtime(nats_url, presence_ttl=3), Runtime(nats_url, presence_ttl=3)
    await a.add(first)
    await eventually(lambda: len(first.publishing_shards) == 4)
    await b.add(second)
    await eventually(
      lambda: len(first.publishing_shards) == 2 and len(second.publishing_shards) == 2
    )
    assert set(first.publishing_shards) | set(second.publishing_shards) == {0, 1, 2, 3}

    # Crash: no drain, no lease cleanup.
    await first._cancel_tasks()  # pyright: ignore[reportPrivateUsage]
    await a.nats.close()
    await eventually(lambda: second.publishing_shards == (0, 1, 2, 3))
    await a.close()
    await b.drain()
    await b.close()

  asyncio.run(exercise())


def test_draining_hands_shards_over_before_leaving(nats_url: str) -> None:
  async def exercise() -> None:
    first, second = worker(shards=2), worker(shards=2)
    a, b = Runtime(nats_url), Runtime(nats_url)
    await a.add(first)
    await b.add(second)
    await eventually(
      lambda: len(first.publishing_shards) == 1 and len(second.publishing_shards) == 1
    )
    await a.drain()
    # Drain returned only after the peer took the shard over.
    assert second.publishing_shards == (0, 1)
    assert first.publishing_shards == ()
    await a.close()
    await b.drain()
    await b.close()

  asyncio.run(exercise())


def test_new_generation_rolls_in_then_takes_over_publishing(nats_url: str) -> None:
  async def exercise() -> None:
    gateway = worker(shards=1)
    async with Runtime(nats_url) as runtime:
      await runtime.add(gateway)
      await eventually(lambda: gateway.publishing_shards == (0,))
      control = GatewayControl(runtime)
      generation = await control.set_shard_count(3)
      assert (generation.id, generation.shard_count) == (2, 3)
      await eventually(lambda: gateway.publishing_shards == (0, 1, 2))
      await eventually(lambda: not live(1))
      assert all(s.closed for s in SESSIONS if s.generation == 1)
      status = await control.status()
      assert status.active == generation
      assert set(status.leases) == {"2.0", "2.1", "2.2"}

  asyncio.run(exercise())


def test_control_requests_reach_the_owning_shard_and_presence_is_global(
  nats_url: str,
) -> None:
  async def exercise() -> None:
    gateway = worker(shards=2)
    async with Runtime(nats_url) as runtime:
      await runtime.add(gateway)
      await eventually(lambda: gateway.publishing_shards == (0, 1))
      control = GatewayControl(runtime)
      guild = 1 << 22  # shard 1 of 2
      await control.request_guild_members(guild, query="", limit=0)
      await control.update_voice_state(guild, None)
      owner = next(s for s in live() if s.shard_id == 1)
      assert owner.members[0].guild_id == guild
      assert owner.voice[0].guild_id == guild
      await control.update_presence(status="idle")
      await eventually(lambda: all(s.presence for s in live()))

  asyncio.run(exercise())


def test_guild_extraction() -> None:
  assert guild_of("MESSAGE_CREATE", {"guild_id": "5"}) == "5"
  assert guild_of("GUILD_CREATE", {"id": "6"}) == "6"
  assert guild_of("READY", {"id": "7"}) is None
  assert json.loads(json.dumps({"x": 1})) == {"x": 1}
