import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, JsonValue

from micro import subjects

from ._table import Table

if TYPE_CHECKING:
  from micro.runtime import Runtime

DECLARATIONS_KEY = "declarations"
"""Presence metadata key: `{kind: {key: hash}}` for each live replica."""


def digest(document: JsonValue) -> str:
  """A stable content hash of a declaration document."""
  encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
  return hashlib.sha256(encoded).hexdigest()[:24]


class DeclarationState(StrEnum):
  CONVERGED = "converged"
  """Every live declarer agrees on this version."""
  MIXED = "mixed"
  """Live declarers disagree (a rollout is in progress); the applied version stands."""
  RETAINED = "retained"
  """No live replica declares it; the applied version stays until forgotten."""


@dataclass(frozen=True, slots=True)
class Declared:
  key: str
  hash: str
  document: JsonValue
  state: DeclarationState
  live_hashes: frozenset[str]


class _Applied(BaseModel):
  model_config = ConfigDict(extra="ignore", frozen=True)

  key: str
  hash: str


class Declarations:
  """Versioned declarations that converge across rolling updates.

  Replicas store each declaration document once, content-addressed, and
  advertise `{key: hash}` in presence. A consumer (command sync, a store) asks
  for the converged view and records what it applied. A new version takes over
  only when every live declarer agrees on it, so a half-finished rollout, or a
  rollback, never changes what is applied; a replica restarting never removes
  anything.
  """

  def __init__(self, runtime: Runtime, kind: str) -> None:
    self.runtime = runtime
    self.kind = subjects.token(kind)

  async def _documents(self) -> Table[JsonValue]:
    return await self.runtime.table(subjects.STATE_BUCKET, JsonValue)

  async def _applied(self) -> Table[_Applied]:
    return await self.runtime.table(subjects.STATE_BUCKET, _Applied)

  def _document_key(self, hash: str) -> str:
    return f"decl.{self.kind}.{hash}"

  def _applied_key(self, key: str) -> str:
    return f"applied.{self.kind}.{subjects.safe_name(key)}"

  async def store(self, documents: Mapping[str, JsonValue]) -> dict[str, str]:
    """Persist documents (idempotently) and return the `{key: hash}` to advertise."""
    table = await self._documents()
    hashes: dict[str, str] = {}
    for key, document in documents.items():
      value = digest(document)
      await table.create(self._document_key(value), document)
      hashes[key] = value
    return hashes

  def live(self) -> dict[str, frozenset[str]]:
    """Hashes each key is declared with by live replicas right now."""
    seen: dict[str, set[str]] = {}
    for entry in self.runtime.directory.entries():
      declared = entry.metadata.get(DECLARATIONS_KEY)
      if not isinstance(declared, dict):
        continue
      mine = declared.get(self.kind)
      if not isinstance(mine, dict):
        continue
      for key, value in mine.items():
        if isinstance(value, str):
          seen.setdefault(key, set()).add(value)
    return {key: frozenset(values) for key, values in seen.items()}

  async def applied(self) -> dict[str, str]:
    table = await self._applied()
    entries = await table.items(f"applied.{self.kind}.>")
    return {entry.value.key: entry.value.hash for entry in entries.values()}

  async def view(self) -> dict[str, Declared]:
    """The converged view: what should be applied now, per key."""
    live = self.live()
    applied = await self.applied()
    documents = await self._documents()
    view: dict[str, Declared] = {}
    for key in sorted(set(live) | set(applied)):
      hashes = live.get(key, frozenset())
      if len(hashes) == 1:
        (chosen,) = hashes
        state = DeclarationState.CONVERGED
      elif hashes:
        if key not in applied:
          continue  # Two versions arrived at once: wait until they converge.
        chosen, state = applied[key], DeclarationState.MIXED
      else:
        chosen, state = applied[key], DeclarationState.RETAINED
      stored = await documents.get(self._document_key(chosen))
      if stored is None:
        continue
      view[key] = Declared(key, chosen, stored.value, state, hashes)
    return view

  async def mark_applied(self, key: str, hash: str) -> None:
    table = await self._applied()
    await table.put(self._applied_key(key), _Applied(key=key, hash=hash))

  async def forget(self, key: str) -> bool:
    """Drop a retired key so consumers stop applying it."""
    table = await self._applied()
    if await table.get(self._applied_key(key)) is None:
      return False
    return await table.delete(self._applied_key(key))


def declarations_metadata(groups: Mapping[str, Mapping[str, str]]) -> dict[str, Any]:
  """Presence metadata advertising `{kind: {key: hash}}`."""
  return {DECLARATIONS_KEY: {kind: dict(values) for kind, values in groups.items()}}
