from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from re import fullmatch
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator

type JsonValue = (
  None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
type JsonSchema = bool | Mapping[str, JsonValue]

_EVENT_ID_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


class ScopeKind(StrEnum):
  GLOBAL = "global"
  GUILD = "guild"
  SHARD = "shard"
  KEYED = "keyed"


@dataclass(frozen=True, slots=True)
class EventScope:
  kind: ScopeKind = ScopeKind.GLOBAL
  field: str | None = None

  def __post_init__(self) -> None:
    if self.kind is ScopeKind.GLOBAL:
      if self.field is not None:
        raise ValueError("A global event scope cannot have a field.")
    elif not self.field:
      raise ValueError(f"A {self.kind.value} event scope requires a field.")

  @classmethod
  def guild(cls, field: str = "guild_id") -> EventScope:
    return cls(ScopeKind.GUILD, field)

  @classmethod
  def shard(cls, field: str = "shard_id") -> EventScope:
    return cls(ScopeKind.SHARD, field)

  @classmethod
  def keyed(cls, field: str) -> EventScope:
    return cls(ScopeKind.KEYED, field)

  def document(self) -> dict[str, JsonValue]:
    document: dict[str, JsonValue] = {"kind": self.kind.value}
    if self.field is not None:
      document["field"] = self.field
    return document


def _identity(value: Any) -> Any:
  return value


@dataclass(frozen=True, slots=True)
class EventSchema[T]:
  id: str
  payload: JsonSchema
  scope: EventScope = field(default_factory=EventScope)
  path: str | None = None
  decoder: Callable[[JsonValue], T] = _identity
  _validator: Validator = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    if fullmatch(_EVENT_ID_PATTERN, self.id) is None:
      raise ValueError(
        "Event schema IDs must contain only letters, numbers, dots, underscores, "
        "and hyphens, and must start and end with a letter or number."
      )
    path = self.path
    if path is not None and (not path.startswith("/") or path.startswith("//")):
      raise ValueError("Custom event paths must be absolute URL paths.")

    payload = deepcopy(
      dict(self.payload) if isinstance(self.payload, Mapping) else self.payload
    )
    Draft202012Validator.check_schema(payload)
    object.__setattr__(
      self,
      "payload",
      MappingProxyType(payload) if isinstance(payload, dict) else payload,
    )
    object.__setattr__(self, "_validator", Draft202012Validator(payload))

  @property
  def endpoint(self) -> str:
    return self.path or f"/events/{self.id}"

  def validate(self, value: JsonValue) -> None:
    self._validator.validate(value)

  def decode(self, value: JsonValue) -> T:
    return self.decoder(value)

  def document(self) -> dict[str, JsonValue]:
    payload = (
      deepcopy(dict(self.payload))
      if isinstance(self.payload, Mapping)
      else self.payload
    )
    return {
      "id": self.id,
      "path": self.endpoint,
      "scope": self.scope.document(),
      "payload": payload,
    }
