import asyncio
import math
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from nats.js.errors import KeyWrongLastSequenceError, NotFoundError
from nats.js.kv import KeyValue
from pydantic import TypeAdapter, ValidationError

_PURGE_OPERATIONS = frozenset(("DEL", "PURGE"))


@dataclass(frozen=True, slots=True)
class Versioned[T]:
  """A table value with the revision that wrote it (for compare-and-set)."""

  value: T
  revision: int


@dataclass(frozen=True, slots=True)
class Change[T]:
  """One table change; `value` is None when the key was deleted or expired."""

  key: str
  value: T | None
  revision: int
  error: ValidationError | None = None
  """Set (with `value` None) by a `lenient` watch when the stored value is invalid."""


class Table[T]:
  """A typed key/value table with compare-and-set and optional per-key TTLs.

  Tables are how Micro shares small coordination state between processes. Values
  are validated with Pydantic in both directions.
  """

  def __init__(self, store: KeyValue, value_type: Any) -> None:
    self._store = store
    self._adapter = TypeAdapter[T](value_type)

  @property
  def bucket(self) -> str:
    """The name of the NATS key-value bucket behind this table."""
    return self._store._name  # pyright: ignore[reportPrivateUsage]

  async def get(self, key: str) -> Versioned[T] | None:
    """The value and revision at `key`, or None if there is none."""
    latest = await self._latest(key)
    if latest is None or latest[1] is None:
      return None
    return Versioned(self._adapter.validate_json(latest[1]), latest[0])

  async def _latest(self, key: str) -> tuple[int, bytes | None] | None:
    """The key's last revision and value (None for a deletion or expiry marker)."""
    js = self._store._js  # pyright: ignore[reportPrivateUsage]
    subject = f"{self._store._pre}{key}"  # pyright: ignore[reportPrivateUsage]
    try:
      message = await js.get_msg(
        self._store._stream,  # pyright: ignore[reportPrivateUsage]
        subject=subject,
        direct=self._store._direct,  # pyright: ignore[reportPrivateUsage]
      )
    except NotFoundError:
      return None
    headers = message.headers or {}
    if (
      headers.get("KV-Operation") in _PURGE_OPERATIONS
      or "Nats-Marker-Reason" in headers
    ):
      return message.seq or 0, None
    return message.seq or 0, message.data or b""

  async def put(self, key: str, value: T) -> int:
    """Write `key` unconditionally; returns the new revision."""
    return await self._store.put(key, self._encode(value))

  async def put_with_ttl(self, key: str, value: T, ttl: float) -> int:
    """Write a key unconditionally; it disappears unless rewritten within `ttl`."""
    js = self._store._js  # pyright: ignore[reportPrivateUsage]
    prefix = self._store._pre  # pyright: ignore[reportPrivateUsage]
    ack = await js.publish(f"{prefix}{key}", self._encode(value), msg_ttl=_ttl(ttl))
    return ack.seq

  async def create(self, key: str, value: T, *, ttl: float | None = None) -> int | None:
    """Write a key only if it does not exist; return None if it does."""
    encoded = self._encode(value)
    while True:
      try:
        return await self._store._update(  # pyright: ignore[reportPrivateUsage]
          key, encoded, last=0, msg_ttl=_ttl(ttl)
        )
      except KeyWrongLastSequenceError:
        pass
      # The key has history; it is free only if its last entry is a deletion.
      latest = await self._latest(key)
      if latest is None:
        continue  # Expired and removed between the two calls; create afresh.
      revision, current = latest
      if current is not None:
        return None
      try:
        return await self._store._update(  # pyright: ignore[reportPrivateUsage]
          key, encoded, last=revision, msg_ttl=_ttl(ttl)
        )
      except KeyWrongLastSequenceError:
        return None

  async def update(
    self, key: str, value: T, *, revision: int, ttl: float | None = None
  ) -> int | None:
    """Replace a key only at `revision`; return None if someone else wrote it."""
    try:
      return await self._store._update(  # pyright: ignore[reportPrivateUsage]
        key, self._encode(value), last=revision, msg_ttl=_ttl(ttl)
      )
    except KeyWrongLastSequenceError:
      return None

  async def delete(self, key: str, *, revision: int | None = None) -> bool:
    """Delete `key` (only at `revision`, if given). Returns whether it deleted."""
    try:
      return await self._store.delete(key, last=revision)
    except KeyWrongLastSequenceError:
      return False

  async def _open(self, keys: str) -> KeyValue.KeyWatcher:
    """Start a watcher that is never left half-made if we are cancelled meanwhile.

    nats-py finishes subscribing in the background; a watcher abandoned mid-setup
    stays subscribed and logs a timeout on the next change.
    """
    creating = asyncio.ensure_future(self._store.watch(keys))
    try:
      return await asyncio.shield(creating)
    except asyncio.CancelledError:
      creating.add_done_callback(self._discard_when_created)
      raise

  async def _discard(self, watcher: KeyValue.KeyWatcher) -> None:
    """Stop a watcher and delete its consumer.

    `stop()` only unsubscribes; the server keeps the (ordered) consumer for
    minutes, and every read or watch leaves one behind, up to JetStream's limit.
    """
    store = self._store
    with suppress(Exception):
      sub: Any = watcher._sub  # pyright: ignore[reportPrivateUsage]
      if sub is None:
        return
      name = (await sub.consumer_info()).name
      await watcher.stop()
      await store._js.delete_consumer(store._stream, name)  # pyright: ignore[reportPrivateUsage]
      return
    with suppress(Exception):
      await watcher.stop()

  def _discard_when_created(self, creating: asyncio.Future[Any]) -> None:
    if creating.cancelled() or creating.exception() is not None:
      return
    task = asyncio.ensure_future(self._discard(creating.result()))
    _stopping.add(task)
    task.add_done_callback(_stopping.discard)

  async def items(self, keys: str = ">") -> dict[str, Versioned[T]]:
    """Current values of keys matching `keys` (NATS wildcards allowed)."""
    watcher = await self._open(keys)
    items: dict[str, Versioned[T]] = {}
    try:
      async for entry in watcher:
        if entry is None:
          break
        if entry.operation in _PURGE_OPERATIONS or entry.value is None:
          items.pop(entry.key, None)
        elif entry.revision is not None:
          items[entry.key] = Versioned(
            self._adapter.validate_json(entry.value), entry.revision
          )
        if entry.delta == 0:
          break
    finally:
      await asyncio.shield(self._discard(watcher))
    return items

  async def watch(
    self, keys: str = ">", *, lenient: bool = False
  ) -> AsyncIterator[Change[T] | None]:
    """Yield current values, then `None` once caught up, then live changes.

    A stored value that does not validate raises `ValidationError` and ends the
    watch, unless `lenient`: then it is yielded as a `Change` with `value` None and
    `error` set, and the watch carries on.
    """
    watcher = await self._open(keys)
    try:
      async for entry in watcher:
        if entry is None:
          yield None
          continue
        if entry.operation in _PURGE_OPERATIONS or entry.value is None:
          yield Change(entry.key, None, entry.revision or 0)
        else:
          try:
            value = self._adapter.validate_json(entry.value)
          except ValidationError as error:
            if not lenient:
              raise
            yield Change(entry.key, None, entry.revision or 0, error)
            continue
          yield Change(entry.key, value, entry.revision or 0)
    finally:
      await asyncio.shield(self._discard(watcher))

  def _encode(self, value: T) -> bytes:
    return self._adapter.dump_json(self._adapter.validate_python(value))


_stopping: set[asyncio.Task[None]] = set()


def _ttl(ttl: float | None) -> float | None:
  if ttl is None:
    return None
  if ttl <= 0:
    raise ValueError("TTL must be positive.")
  # The server accepts whole seconds; never round a TTL down to zero.
  return float(max(1, math.ceil(ttl)))
