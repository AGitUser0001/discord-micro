import asyncio

from pydantic import BaseModel

from micro import subjects
from micro.runtime import Component, ComponentState, Runtime


class Counter(BaseModel):
  value: int


class Probe(Component):
  kind = "probe"

  def __init__(self) -> None:
    super().__init__("probe")
    self.events: list[str] = []

  async def on_start(self) -> None:
    self.events.append("start")
    await self.runtime.register(self, metadata={"answer": 42})

  async def on_drain(self) -> None:
    self.events.append("drain")

  async def on_close(self) -> None:
    self.events.append("close")


def test_runtime_hosts_components_and_publishes_presence(nats_url: str) -> None:
  async def exercise() -> None:
    probe = Probe()
    async with Runtime(nats_url) as runtime:
      await runtime.add(probe)
      await runtime.directory.wait_for(lambda d: bool(d.entries("probe")))
      (entry,) = runtime.directory.entries("probe")
      assert entry.metadata == {"answer": 42}
      assert entry.instance == runtime.instance
      async with Runtime(nats_url) as observer:
        assert [e.name for e in observer.directory.entries("probe")] == ["probe"]
        await runtime.drain()
        await runtime.close()
        await observer.directory.wait_for(lambda d: not d.entries("probe"))
    assert probe.events == ["start", "drain", "close"]
    assert probe.phase is ComponentState.CLOSED

  asyncio.run(exercise())


def test_tables_compare_and_set_and_expire(nats_url: str) -> None:
  async def exercise() -> None:
    async with Runtime(nats_url) as runtime:
      table = await runtime.table(subjects.STATE_BUCKET, Counter)
      first = await table.create("count", Counter(value=1))
      assert first is not None
      assert await table.create("count", Counter(value=2)) is None
      assert await table.update("count", Counter(value=3), revision=first + 99) is None
      second = await table.update("count", Counter(value=3), revision=first)
      assert second is not None
      current = await table.get("count")
      assert current is not None and current.value.value == 3
      assert set(await table.items()) == {"count"}

      locks = await runtime.locks()
      assert await locks.try_acquire("job", ttl=1) is not None
      assert await locks.try_acquire("job", ttl=1) is None
      started = asyncio.get_running_loop().time()
      await locks.acquire("job", ttl=1)
      assert asyncio.get_running_loop().time() - started >= 0.5
      async with locks.hold("sync", ttl=3):
        assert await locks.try_acquire("sync", ttl=3) is None
      assert await locks.try_acquire("sync", ttl=3) is not None

  asyncio.run(exercise())
