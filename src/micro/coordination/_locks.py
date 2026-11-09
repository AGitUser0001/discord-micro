import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from pydantic import BaseModel, ConfigDict

from ._table import Table

logger = logging.getLogger("micro")


class LockHolder(BaseModel):
  model_config = ConfigDict(extra="ignore", frozen=True)

  owner: str


class LockLost(RuntimeError):
  """A held lock expired or was taken before its holder released it."""


class Locks:
  """Cluster-wide leases with a TTL, built on a table.

  `gate` takes a lease and lets it expire, which spaces out work such as Discord
  identifies. `hold` keeps a lease renewed while a job runs.
  """

  def __init__(self, table: Table[LockHolder], owner: str) -> None:
    self._table = table
    self.owner = owner

  async def try_acquire(self, name: str, *, ttl: float) -> int | None:
    """Take the lease if it is free and return its revision; None if someone holds it."""
    return await self._table.create(name, LockHolder(owner=self.owner), ttl=ttl)

  async def acquire(self, name: str, *, ttl: float) -> int:
    """Wait until the lease is free, then take it."""
    while True:
      revision = await self.try_acquire(name, ttl=ttl)
      if revision is not None:
        return revision
      await self._wait_free(name)

  async def gate(self, name: str, *, ttl: float) -> None:
    """Take a lease and leave it to expire: at most one caller per `ttl`."""
    await self.acquire(name, ttl=ttl)

  @asynccontextmanager
  async def hold(self, name: str, *, ttl: float) -> AsyncIterator[None]:
    """Hold the lease while the block runs, renewing it; raises `LockLost` afterwards if it was taken meanwhile."""
    revision = await self.acquire(name, ttl=ttl)
    lost = asyncio.Event()

    async def renew() -> None:
      nonlocal revision
      while True:
        await asyncio.sleep(ttl / 3)
        try:
          renewed = await self._table.update(
            name, LockHolder(owner=self.owner), revision=revision, ttl=ttl
          )
        except asyncio.CancelledError:
          raise
        except Exception:
          # Could not reach NATS: try again. If the lease expires meanwhile the
          # next successful attempt finds it gone and reports the loss.
          logger.warning("Could not renew lock %s", name, exc_info=True)
          continue
        if renewed is None:
          lost.set()
          return
        revision = renewed

    renewer = asyncio.create_task(renew(), name=f"micro.lock.{name}")
    try:
      yield
    finally:
      renewer.cancel()
      with suppress(asyncio.CancelledError):
        await renewer
      if not lost.is_set():
        try:
          released = await self._table.delete(name, revision=revision)
        except Exception:
          logger.warning("Could not release lock %s; it expires by itself", name)
        else:
          if not released:
            lost.set()  # someone else holds it now: it expired while we worked
    if lost.is_set():
      raise LockLost(f"Lock {name!r} was lost while held.")

  async def _wait_free(self, name: str) -> None:
    async for change in self._table.watch(name):
      if change is None:
        if await self._table.get(name) is None:
          return
        continue
      if change.value is None:
        return
