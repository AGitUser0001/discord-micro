import asyncio
import logging
from collections.abc import Callable
from contextlib import suppress
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from micro import subjects
from micro.coordination import Table

logger = logging.getLogger("micro")


class Registration(BaseModel):
  """What one live component advertises to the rest of the deployment."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  kind: str = Field(min_length=1)
  name: str = Field(min_length=1)
  instance: str = Field(min_length=1)
  """The runtime (process) hosting the component."""
  id: str = Field(min_length=1)
  """Unique per registration; also the component's routing address."""
  metadata: dict[str, JsonValue] = Field(default_factory=dict)


class Presence:
  """A component's renewing registration in the presence table."""

  def __init__(
    self, table: Table[Registration], registration: Registration, ttl: float
  ) -> None:
    self._table = table
    self.registration = registration
    self._ttl = ttl
    self._key = (
      f"{subjects.dotted(registration.kind)}.{subjects.token(registration.id)}"
    )
    self._revision: int | None = None
    self._renewer: asyncio.Task[None] | None = None

  async def start(self) -> None:
    self._revision = await self._table.put_with_ttl(
      self._key, self.registration, self._ttl
    )
    self._renewer = asyncio.create_task(
      self._renew(), name=f"micro.presence.{self._key}"
    )

  async def update(self, metadata: dict[str, JsonValue]) -> None:
    self.registration = self.registration.model_copy(update={"metadata": metadata})
    self._revision = await self._table.put_with_ttl(
      self._key, self.registration, self._ttl
    )

  async def stop(self) -> None:
    if self._renewer is not None:
      self._renewer.cancel()
      with suppress(asyncio.CancelledError):
        await self._renewer
      self._renewer = None
    with suppress(Exception):
      await self._table.delete(self._key)

  async def _renew(self) -> None:
    while True:
      await asyncio.sleep(self._ttl / 3)
      try:
        self._revision = await self._table.put_with_ttl(
          self._key, self.registration, self._ttl
        )
      except asyncio.CancelledError:
        raise
      except Exception:
        logger.warning("Could not renew presence %s", self._key, exc_info=True)


class Directory:
  """A live, watch-driven view of every registered component."""

  def __init__(self, table: Table[Registration]) -> None:
    self._table = table
    self._entries: dict[str, Registration] = {}
    self._listeners: list[Callable[[], Any]] = []
    self._synced = asyncio.Event()
    self._changed = asyncio.Condition()
    self._task: asyncio.Task[None] | None = None

  async def start(self) -> None:
    self._task = asyncio.create_task(self._watch(), name="micro.directory")
    await self._synced.wait()

  async def close(self) -> None:
    if self._task is not None:
      self._task.cancel()
      with suppress(asyncio.CancelledError):
        await self._task
      self._task = None

  def entries(self, kind: str | None = None) -> tuple[Registration, ...]:
    values = self._entries.values()
    if kind is None:
      return tuple(values)
    return tuple(entry for entry in values if entry.kind == kind)

  def on_change(self, listener: Callable[[], Any]) -> Callable[[], None]:
    """Call `listener` after every change; returns a function removing it."""
    self._listeners.append(listener)
    return lambda: self._listeners.remove(listener)

  async def wait_for(self, predicate: Callable[[Directory], bool]) -> None:
    async with self._changed:
      await self._changed.wait_for(lambda: predicate(self))

  async def _watch(self) -> None:
    while True:
      try:
        async for change in self._table.watch():
          if change is None:
            self._synced.set()
          elif change.value is None:
            self._entries.pop(change.key, None)
          else:
            self._entries[change.key] = change.value
          if self._synced.is_set():
            await self._notify()
      except asyncio.CancelledError:
        raise
      except Exception:
        logger.warning("Presence watch failed; restarting", exc_info=True)
        await asyncio.sleep(1)

  async def _notify(self) -> None:
    async with self._changed:
      self._changed.notify_all()
    for listener in tuple(self._listeners):
      try:
        listener()
      except Exception:
        logger.exception("Directory listener failed")


def registration_id() -> str:
  return uuid4().hex
