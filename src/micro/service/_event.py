from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from re import fullmatch
from typing import Any, cast

from pydantic import TypeAdapter

type JsonValue = (
  None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
type JsonSchema = bool | dict[str, JsonValue]

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


@dataclass(frozen=True, slots=True)
class EventSchema[T]:
  id: str
  payload: Any
  scope: EventScope = field(default_factory=EventScope)
  path: str | None = None
  _adapter: TypeAdapter[T] = field(init=False, repr=False, compare=False)
  _payload_schema: dict[str, JsonValue] = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    if fullmatch(_EVENT_ID_PATTERN, self.id) is None:
      raise ValueError(
        "Event schema IDs must contain only letters, numbers, dots, underscores, "
        "and hyphens, and must start and end with a letter or number."
      )
    if self.path is not None and (
      not self.path.startswith("/") or self.path.startswith("//")
    ):
      raise ValueError("Custom event paths must be absolute URL paths.")

    adapter = TypeAdapter[T](self.payload)
    object.__setattr__(self, "_adapter", adapter)
    object.__setattr__(
      self,
      "_payload_schema",
      cast(dict[str, JsonValue], adapter.json_schema(mode="validation")),
    )

  @property
  def endpoint(self) -> str:
    return self.path or f"/events/{self.id}"

  def decode(self, value: JsonValue) -> T:
    return self._adapter.validate_python(value)

  def encode(self, value: T) -> JsonValue:
    validated = self._adapter.validate_python(value)
    return cast(JsonValue, self._adapter.dump_python(validated, mode="json"))

  def document(self) -> dict[str, JsonValue]:
    return {
      "id": self.id,
      "path": self.endpoint,
      "scope": self.scope.document(),
      "payload": deepcopy(self._payload_schema),
    }
