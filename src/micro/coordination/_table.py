import asyncio
import math
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from nats.js.errors import (
  KeyDeletedError,
  KeyNotFoundError,
  KeyWrongLastSequenceError,
)
from nats.js.kv import KeyValue
from pydantic import TypeAdapter

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
    return self._store._name  # pyright: ignore[reportPrivateUsage]

  async def get(self, key: str) -> Versioned[T] | None:
    try:
      entry = await self._store.get(key)
    except KeyNotFoundError, KeyDeletedError:
      return None
    if entry.value is None or entry.revision is None:
      return None
    return Versioned(self._adapter.validate_json(entry.value), entry.revision)

  async def put(self, key: str, value: T) -> int:
    return await self._store.put(key, self._encode(value))

  async def put_with_ttl(self, key: str, value: T, ttl: float) -> int:
    """Write a key unconditionally; it disappears unless rewritten within `ttl`."""
    js = self._store._js  # pyright: ignore[reportPrivateUsage]
    prefix = self._store._pre  # pyright: ignore[reportPrivateUsage]
    ack = await js.publish(f"{prefix}{key}", self._encode(value), msg_ttl=_ttl(ttl))
    return ack.seq

  async def create(self, key: str, value: T, *, ttl: float | None = None) -> int | None:
    """Write a key only if it does not exist; return None if it does."""
    try:
      return await self._store.create(key, self._encode(value), msg_ttl=_ttl(ttl))
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
    try:
      return await self._store.delete(key, last=revision)
    except KeyWrongLastSequenceError:
      return False

  async def items(self) -> dict[str, Versioned[T]]:
    watcher = await self._store.watchall()
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
      await watcher.stop()
    return items

  async def watch(self, keys: str = ">") -> AsyncIterator[Change[T] | None]:
    """Yield current values, then `None` once caught up, then live changes."""
    watcher = await self._store.watch(keys)
    try:
      async for entry in watcher:
        if entry is None:
          yield None
          continue
        if entry.operation in _PURGE_OPERATIONS or entry.value is None:
          yield Change(entry.key, None, entry.revision or 0)
        else:
          yield Change(
            entry.key, self._adapter.validate_json(entry.value), entry.revision or 0
          )
    finally:
      await asyncio.shield(watcher.stop())

  def _encode(self, value: T) -> bytes:
    return self._adapter.dump_json(self._adapter.validate_python(value))


def _ttl(ttl: float | None) -> float | None:
  if ttl is None:
    return None
  if ttl <= 0:
    raise ValueError("TTL must be positive.")
  # The server accepts whole seconds; never round a TTL down to zero.
  return float(max(1, math.ceil(ttl)))
