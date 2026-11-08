"""Distributed configuration: a typed document every process keeps in sync.

    class Limits(BaseModel):
      model_config = ConfigDict(frozen=True)
      rate: int = 10

    limits = await runtime.config("limits", Limits)      # shared across the deployment
    limits.value.rate                                    # this process's snapshot
    await limits.update(rate=20)                         # every process follows

A `Config` is one Pydantic document in a NATS key-value bucket. The first process to
start writes the initial document atomically; after that the stored document is the
truth, writes are compare-and-set, and every process (including the writer) watches the
key and moves its local snapshot to each new revision. Before the snapshot is replaced,
the new document goes through *refresh middleware* that may do work, reject the change,
or defer it; a refresh that fails leaves the old snapshot in place and is retried.
There is no config server and no broadcast: the watch on the bucket is the only channel.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from micro import subjects
from micro.coordination import Table, Versioned
from micro.errors import MicroError
from micro.middleware import Middleware, Middlewares
from micro.runtime import default_backoff

if TYPE_CHECKING:
  from micro.runtime import Runtime

logger = logging.getLogger("micro")


class ConfigError(MicroError):
  """Base of configuration failures."""


class ConfigRejected(ConfigError):
  """Refresh middleware refused a revision: it is dropped and never retried."""

  def __init__(self, reason: str, *, revision: int | None = None) -> None:
    self.reason = reason
    self.revision = revision
    super().__init__(reason)


class ConfigDeferred(ConfigError):
  """Refresh middleware postponed a revision: it is retried, not dropped."""

  def __init__(self, delay: float | None = None) -> None:
    self.delay = delay
    super().__init__("deferred" if delay is None else f"deferred for {delay}s")


class ConfigConflict(ConfigError):
  """A write named a revision that is no longer current."""

  def __init__(self, name: str, expected: int, current: int | None) -> None:
    self.expected = expected
    self.current = current
    super().__init__(
      f"Config {name!r} is at revision {current}, not {expected}; read it again."
    )


class ConfigMissing(ConfigError):
  """The document does not exist and there was nothing to start it from."""


class ConfigInvalid(ConfigError):
  """The stored document does not validate against the model."""


class ConfigClosed(ConfigError):
  """The config was closed while something waited on it."""


@dataclass(slots=True)
class Refresh[T: BaseModel]:
  """A change about to be applied: what refresh middleware receives.

  `old` is the current snapshot and `new` the incoming document at `revision`.
  Call `next()` to continue (the change is applied once the whole chain returns).
  Raise `refresh.reject(why)` to drop this revision for good, `refresh.defer()` to
  hold it back and retry (after `delay` seconds, or on the next change or `retry()`).
  Anything else that is raised leaves the snapshot alone and retries with a backoff,
  so side effects must be safe to run more than once.
  """

  name: str
  old: T
  new: T
  revision: int
  previous: int | None
  """The revision of `old`, or None while it is still the bootstrap value."""
  attempt: int = 1
  """1 on the first try of this revision, counting up on retries."""
  initial: bool = False
  """True for the first document this process loads, replacing the bootstrap value."""
  reached: bool = False

  @property
  def key(self) -> str:
    """The config name (what the middleware engine scopes on)."""
    return self.name

  @property
  def changed(self) -> dict[str, tuple[Any, Any]]:
    """Fields that differ, as `{field: (old, new)}`."""
    before, after = self.old.model_dump(), self.new.model_dump()
    return {k: (before.get(k), after[k]) for k in after if before.get(k) != after[k]}

  def reject(self, reason: str) -> ConfigRejected:
    """`raise refresh.reject("why")`: drop this revision."""
    return ConfigRejected(reason, revision=self.revision)

  def defer(self, delay: float | None = None) -> ConfigDeferred:
    """`raise refresh.defer(5)`: keep the old snapshot and try this revision again."""
    return ConfigDeferred(delay)


@dataclass(frozen=True, slots=True)
class Applied[T: BaseModel]:
  """A snapshot change that took effect."""

  old: T
  new: T
  revision: int


@dataclass(frozen=True, slots=True)
class ConfigIssue:
  """Something that stopped a revision from being applied (or the watch from running)."""

  kind: str
  """`rejected`, `deferred`, `failed`, `invalid`, `deleted` or `watch`."""
  revision: int | None
  error: BaseException | str


type Listener[T: BaseModel] = Callable[[Applied[T]], Awaitable[None] | None]
type ErrorListener = Callable[[ConfigIssue], Awaitable[None] | None]


@dataclass(slots=True)
class _Waiter:
  revision: int
  future: asyncio.Future[Versioned[Any]]


class Config[T: BaseModel]:
  """One typed, shared configuration document. See the module docstring.

  `bootstrap` is this process's own idea of the settings (from its environment or
  code): it is what `value` returns before the first load, and the document written
  when none exists yet (unless `seed=False`). Keep the settings needed to *reach* NATS
  out of the document: they stay local and are available immediately.
  """

  def __init__(
    self,
    runtime: Runtime,
    name: str,
    model: type[T],
    *,
    bootstrap: T | Callable[[], T] | None = None,
    seed: bool = True,
  ) -> None:
    self.runtime = runtime
    self.name = subjects.token(name)
    self.model = model
    self._bootstrap = bootstrap
    self._seed = seed
    self._middleware: Middlewares[Refresh[T]] = Middlewares()
    self._table: Table[T] | None = None
    self._snapshot: Versioned[T] | None = None
    self._local: T | None = None
    self._incoming: Versioned[T] | None = None
    self._rejected: set[int] = set()
    self._wake = asyncio.Event()
    self._retry_in: float | None = None
    self._attempt = 0
    self._failures = 0
    self._tasks: list[asyncio.Task[None]] = []
    self._started = False
    self._closed = False
    self._listeners: list[Listener[T]] = []
    self._error_listeners: list[ErrorListener] = []
    self._watchers: list[asyncio.Queue[Applied[T] | None]] = []
    self._waiters: list[_Waiter] = []
    self.last_error: ConfigIssue | None = None
    """The most recent issue, kept for inspection."""

  # Reading ---------------------------------------------------------------------

  @property
  def value(self) -> T:
    """This process's current snapshot (the bootstrap value until the first load)."""
    if self._snapshot is not None:
      return self._snapshot.value
    return self._bootstrap_value()

  @property
  def revision(self) -> int | None:
    """The revision of the snapshot, or None while it is still the bootstrap value."""
    return self._snapshot.revision if self._snapshot is not None else None

  @property
  def loaded(self) -> bool:
    """Whether the snapshot comes from the shared document."""
    return self._snapshot is not None

  def _bootstrap_value(self) -> T:
    if self._local is None:
      source = self._bootstrap
      if source is None:
        self._local = self.model()
      else:
        self._local = source() if callable(source) else source
    return self._local

  # Middleware, listeners ------------------------------------------------------------

  def use(self, function: Middleware, /) -> Middleware:
    """Add refresh middleware: `async def f(refresh, next)`, outermost first.

    It runs for every incoming revision before the snapshot is replaced, including the
    first document this process loads. See `Refresh` for the three ways it can end.
    """
    return self._middleware.use(function)

  def on_change(self, listener: Listener[T]) -> Callable[[], None]:
    """Call `listener(applied)` after each snapshot change. Returns a remover.

    Listeners run in order, after the change took effect, and their errors are
    logged without affecting anything.
    """
    self._listeners.append(listener)
    return lambda: (
      self._listeners.remove(listener) if listener in self._listeners else None
    )

  def on_error(self, listener: ErrorListener) -> Callable[[], None]:
    """Call `listener(issue)` for each rejection, deferral, failure or invalid value."""
    self._error_listeners.append(listener)
    return lambda: (
      self._error_listeners.remove(listener)
      if listener in self._error_listeners
      else None
    )

  async def watch(self, *, initial: bool = False) -> AsyncIterator[Applied[T]]:
    """Yield each snapshot change as it is applied (and, with `initial`, the current one first).

    The iterator ends when the config closes. Changes queue up if you read slowly.
    """
    queue: asyncio.Queue[Applied[T] | None] = asyncio.Queue()
    self._watchers.append(queue)
    try:
      if initial and self._snapshot is not None:
        yield Applied(
          self._snapshot.value, self._snapshot.value, self._snapshot.revision
        )
      while True:
        item = await queue.get()
        if item is None:
          return
        yield item
    finally:
      with suppress(ValueError):
        self._watchers.remove(queue)

  # Lifecycle -------------------------------------------------------------------

  async def start(self) -> Config[T]:
    """Open the bucket, create the document if missing, load it, and begin watching.

    Safe to call twice. The first load runs the refresh middleware like any change; if
    that rejects, defers or fails, the bootstrap value stays and the background loop
    carries on, so `start` does not hang on a slow middleware.
    """
    if self._started:
      return self
    if self._closed:
      raise ConfigClosed(f"Config {self.name!r} is closed.")
    self._table = await self.runtime.table(subjects.CONFIG_BUCKET, self.model)
    current = await self._load_or_create()
    self._started = True
    self._observe(current)
    await self._process(initial=True)
    self._wake.clear()  # the loop starts on this attempt's backoff, not at once
    self._tasks = [
      asyncio.create_task(self._watch_loop(), name=f"micro.config.{self.name}.watch"),
      asyncio.create_task(self._apply_loop(), name=f"micro.config.{self.name}.apply"),
    ]
    return self

  async def close(self) -> None:
    """Stop watching, release waiters and end `watch()` iterators."""
    if self._closed:
      return
    self._closed = True
    for task in self._tasks:
      task.cancel()
    for task in self._tasks:
      with suppress(asyncio.CancelledError, Exception):
        await task
    self._tasks.clear()
    for waiter in self._waiters:
      if not waiter.future.done():
        waiter.future.set_exception(ConfigClosed(f"Config {self.name!r} closed."))
    self._waiters.clear()
    for queue in self._watchers:
      queue.put_nowait(None)

  async def __aenter__(self) -> Config[T]:
    return await self.start()

  async def __aexit__(self, *exc: object) -> None:
    await self.close()

  async def _load_or_create(self) -> Versioned[T]:
    table = self._table_()
    while True:
      try:
        found = await table.get(self.name)
      except ValidationError as error:
        raise ConfigInvalid(
          f"Stored config {self.name!r} does not match {self.model.__name__}: {error}"
        ) from error
      if found is not None:
        return found
      if not self._seed:
        raise ConfigMissing(f"Config {self.name!r} does not exist and seed=False.")
      document = self._bootstrap_value()
      if await table.create(self.name, document) is not None:
        continue  # re-read, so everyone starts from what is stored
      # Someone else created it between our get and create: loop and read theirs.

  def _table_(self) -> Table[T]:
    if self._table is None:
      raise ConfigError(f"Config {self.name!r} has not started.")
    return self._table

  # Writing ---------------------------------------------------------------------

  async def read(self) -> Versioned[T]:
    """The stored document and revision right now (not this process's snapshot)."""
    try:
      found = await self._table_().get(self.name)
    except ValidationError as error:
      raise ConfigInvalid(
        f"Stored config {self.name!r} does not match {self.model.__name__}; "
        f"repair it with set(): {error}"
      ) from error
    if found is None:
      raise ConfigMissing(f"Config {self.name!r} no longer exists.")
    return found

  async def set(self, value: T, *, revision: int | None = None) -> Versioned[T]:
    """Replace the document.

    With `revision`, only if the stored document is still at it (else `ConfigConflict`):
    use it to write what you read without a lost update. Without, it overwrites.
    The value is validated first; nothing is written if it is not valid.
    """
    document = self.model.model_validate(value.model_dump())
    table = self._table_()
    if revision is None:
      return Versioned(document, await table.put(self.name, document))
    written = await table.update(self.name, document, revision=revision)
    if written is None:
      current = await table.get(self.name)
      raise ConfigConflict(self.name, revision, current.revision if current else None)
    return Versioned(document, written)

  async def update(
    self, change: Callable[[T], T] | None = None, /, **fields: Any
  ) -> Versioned[T]:
    """Change the document safely: read, apply, write only if nothing intervened, retry.

    `update(rate=20)` sets fields; `update(lambda c: c.model_copy(update=...))` computes
    the new document from the current one (it may run more than once, so keep it free of
    side effects). Returns what was stored; if the result equals the current document
    nothing is written. The change reaches this process through the same refresh as any
    other: `await config.wait_for(result.revision)` waits for it.
    """
    table = self._table_()
    while True:
      current = await self.read()
      if change is not None:
        candidate = change(current.value)
      else:
        candidate = current.value
      if fields:
        candidate = candidate.model_copy(update=fields)
      document = self.model.model_validate(candidate.model_dump())
      if document == current.value:
        return current
      written = await table.update(self.name, document, revision=current.revision)
      if written is not None:
        return Versioned(document, written)

  async def wait_for(
    self, revision: int, *, timeout: float | None = None
  ) -> Versioned[T]:
    """Wait until the snapshot is at `revision` or newer.

    Raises `ConfigRejected` if that very revision is rejected by the middleware, and
    `ConfigClosed` if the config closes first.
    """
    if self._snapshot is not None and self._snapshot.revision >= revision:
      return self._snapshot
    if revision in self._rejected:
      raise ConfigRejected("rejected", revision=revision)
    waiter = _Waiter(revision, asyncio.get_running_loop().create_future())
    self._waiters.append(waiter)
    try:
      return await asyncio.wait_for(waiter.future, timeout)
    finally:
      with suppress(ValueError):
        self._waiters.remove(waiter)

  def retry(self) -> None:
    """Try the latest incoming revision again now (cuts short a deferral or backoff)."""
    self._attempt = 0
    self._retry_in = None
    self._wake.set()

  # Following the shared document -------------------------------------------------

  def _observe(self, found: Versioned[T]) -> None:
    """Remember the newest revision seen; the apply loop moves the snapshot to it."""
    if self._incoming is None or found.revision > self._incoming.revision:
      self._incoming = found
      self._wake.set()

  async def _watch_loop(self) -> None:
    table = self._table_()
    failures = 0
    while True:
      try:
        async for change in table.watch(self.name, lenient=True):
          failures = 0
          if change is None:
            continue
          if change.error is not None:
            self._report("invalid", change.revision, change.error)
          elif change.value is None:
            self._report("deleted", change.revision, "the stored document was deleted")
          else:
            self._observe(Versioned(change.value, change.revision))
        reason: BaseException | str = "the watch ended"
      except asyncio.CancelledError:
        raise
      except Exception as error:
        reason = error
      self._report("watch", None, reason)
      await asyncio.sleep(default_backoff(failures + 1))
      failures += 1
      # Anything missed while the watch was down is in the stored document.
      with suppress(Exception):
        found = await table.get(self.name)
        if found is not None:
          self._observe(found)

  async def _apply_loop(self) -> None:
    while True:
      try:
        await asyncio.wait_for(self._wake.wait(), self._retry_in)
      except TimeoutError:
        pass
      self._wake.clear()
      await self._process()

  async def _process(self, *, initial: bool = False) -> None:
    incoming = self._incoming
    applied = self._snapshot.revision if self._snapshot is not None else -1
    if (
      incoming is None
      or incoming.revision <= applied
      or incoming.revision in self._rejected
    ):
      self._retry_in = None
      return
    self._attempt += 1
    refresh = Refresh(
      name=self.name,
      old=self.value,
      new=incoming.value,
      revision=incoming.revision,
      previous=self._snapshot.revision if self._snapshot is not None else None,
      attempt=self._attempt,
      initial=initial or self._snapshot is None,
    )
    try:
      await self._middleware.run(refresh, self._finish)
    except asyncio.CancelledError:
      raise
    except ConfigRejected as error:
      self._rejected.add(incoming.revision)
      self._retry_in, self._attempt, self._failures = None, 0, 0
      self._report("rejected", incoming.revision, error)
      self._release(incoming.revision, error)
      return
    except ConfigDeferred as error:
      self._retry_in = error.delay
      self._report("deferred", incoming.revision, error)
      return
    except Exception as error:
      self._failures += 1
      self._retry_in = default_backoff(self._failures)
      self._report("failed", incoming.revision, error)
      return
    if not refresh.reached:
      # A middleware ended the chain without next(): nothing applied, try again later.
      self._retry_in = None
      self._report("deferred", incoming.revision, "ended without applying")
      return
    self._retry_in, self._attempt, self._failures = None, 0, 0
    await self._apply(refresh.old, incoming)

  async def _finish(self, refresh: Refresh[T]) -> None:
    """The end of the chain; the snapshot is replaced after the whole chain returns."""

  async def _apply(self, old: T, incoming: Versioned[T]) -> None:
    self._snapshot = incoming
    event = Applied(old, incoming.value, incoming.revision)
    for waiter in tuple(self._waiters):
      if waiter.revision <= incoming.revision and not waiter.future.done():
        waiter.future.set_result(incoming)
    for queue in self._watchers:
      queue.put_nowait(event)
    for listener in tuple(self._listeners):
      try:
        outcome = listener(event)
        if outcome is not None:
          await outcome
      except Exception:
        logger.exception("Config %s change listener failed", self.name)

  def _release(self, revision: int, error: BaseException) -> None:
    for waiter in tuple(self._waiters):
      if waiter.revision == revision and not waiter.future.done():
        waiter.future.set_exception(error)

  def _report(
    self, kind: str, revision: int | None, error: BaseException | str
  ) -> None:
    issue = ConfigIssue(kind, revision, error)
    self.last_error = issue
    level = logging.INFO if kind in {"deferred", "rejected"} else logging.WARNING
    logger.log(level, "Config %s revision %s %s: %s", self.name, revision, kind, error)
    for listener in tuple(self._error_listeners):
      try:
        outcome = listener(issue)
        if outcome is not None:
          task = asyncio.ensure_future(outcome)
          task.add_done_callback(lambda t: t.exception())
      except Exception:
        logger.exception("Config %s error listener failed", self.name)


__all__ = (
  "Applied",
  "Config",
  "ConfigClosed",
  "ConfigConflict",
  "ConfigDeferred",
  "ConfigError",
  "ConfigInvalid",
  "ConfigIssue",
  "ConfigMissing",
  "ConfigRejected",
  "Refresh",
)
