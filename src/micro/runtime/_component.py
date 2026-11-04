import asyncio
import logging
from collections.abc import AsyncIterator, Coroutine
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from micro.errors import DrainingError

if TYPE_CHECKING:
  from ._runtime import Runtime

logger = logging.getLogger("micro")


class ComponentState(StrEnum):
  CREATED = "created"
  STARTING = "starting"
  RUNNING = "running"
  DRAINING = "draining"
  CLOSED = "closed"


class Component:
  """Something a runtime hosts: a service, a Gateway worker, an HTTP worker.

  Lifecycle: `start` → running → `drain` (stop taking new work, finish in-flight
  work, release leases) → `close`. Subclasses override the `on_*` hooks and use
  `spawn` for background tasks and `work` around each unit of work.
  """

  kind: str = "component"

  def __init__(self, name: str) -> None:
    if not name:
      raise ValueError("Component names cannot be empty.")
    self.name = name
    self.phase = ComponentState.CREATED
    self._runtime: Runtime | None = None
    self._tasks: set[asyncio.Task[Any]] = set()
    self._in_flight = 0
    self._idle = asyncio.Event()
    self._idle.set()

  @property
  def runtime(self) -> Runtime:
    if self._runtime is None:
      raise RuntimeError(f"Component {self.name!r} has not started.")
    return self._runtime

  @property
  def accepting(self) -> bool:
    return self.phase is ComponentState.RUNNING

  @property
  def active(self) -> bool:
    """Whether work sources should keep handing out new work."""
    return self.phase in (ComponentState.STARTING, ComponentState.RUNNING)

  @property
  def ready(self) -> bool:
    """Whether this component can serve work now; subclasses may add checks."""
    return self.accepting

  async def start(self, runtime: Runtime) -> None:
    if self.phase is not ComponentState.CREATED:
      raise RuntimeError(f"Component {self.name!r} cannot start twice.")
    self._runtime = runtime
    self.phase = ComponentState.STARTING
    try:
      await self.on_start()
    except BaseException:
      self.phase = ComponentState.CLOSED
      await self._cancel_tasks()
      raise
    self.phase = ComponentState.RUNNING

  async def drain(self) -> None:
    if self.phase is not ComponentState.RUNNING:
      return
    self.phase = ComponentState.DRAINING
    await self.on_drain()
    await self._idle.wait()

  async def close(self) -> None:
    if self.phase is ComponentState.CLOSED:
      return
    self.phase = ComponentState.CLOSED
    try:
      await self.on_close()
    finally:
      await self._cancel_tasks()

  async def on_start(self) -> None:
    pass

  async def on_drain(self) -> None:
    pass

  async def on_close(self) -> None:
    pass

  def spawn(
    self, coroutine: Coroutine[Any, Any, Any], *, name: str
  ) -> asyncio.Task[Any]:
    """Run a background task owned by this component; failures are logged."""
    task = asyncio.create_task(coroutine, name=f"micro.{self.name}.{name}")
    self._tasks.add(task)
    task.add_done_callback(self._task_done)
    return task

  @asynccontextmanager
  async def tracked(self) -> AsyncIterator[None]:
    """Track one unit of work so draining waits for it.

    Work already received while draining still runs; sources stop handing out
    new work when `accepting` turns false.
    """
    if self.phase in (ComponentState.CREATED, ComponentState.CLOSED):
      raise DrainingError(f"Component {self.name!r} is not accepting work.")
    self._in_flight += 1
    self._idle.clear()
    try:
      yield
    finally:
      self._in_flight -= 1
      if self._in_flight == 0:
        self._idle.set()

  @property
  def in_flight(self) -> int:
    return self._in_flight

  def _task_done(self, task: asyncio.Task[Any]) -> None:
    self._tasks.discard(task)
    if not task.cancelled() and (error := task.exception()) is not None:
      logger.error("Background task %s failed", task.get_name(), exc_info=error)

  async def _cancel_tasks(self) -> None:
    tasks = tuple(self._tasks)
    for task in tasks:
      task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
