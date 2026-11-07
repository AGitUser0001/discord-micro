import json
from dataclasses import dataclass, field
from typing import Any, Self

from pydantic import BaseModel, JsonValue, TypeAdapter

from ._pattern import Route

CUSTOM_ID_LIMIT = 100
"""Discord's maximum custom_id length."""


@dataclass(frozen=True, slots=True)
class CustomId[T: BaseModel](Route):
  """A routed custom_id prefix carrying typed state.

  `encode` writes `prefix:[v1,v2,...]` (field values in declaration order, as
  compact JSON), so state costs only its values. The prefix routes the
  interaction to the service that declared this CustomId.
  """

  prefix: str
  state: type[T] | None = None
  _fields: tuple[str, ...] = field(init=False, repr=False, compare=False)
  _adapter: TypeAdapter[Any] = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    if not self.prefix or ":" in self.prefix:
      raise ValueError("A custom_id prefix must be non-empty and contain no ':'.")
    if len(self.prefix) > CUSTOM_ID_LIMIT:
      raise ValueError("A custom_id prefix cannot exceed 100 characters.")
    fields = tuple(self.state.model_fields) if self.state is not None else ()
    object.__setattr__(self, "_fields", fields)
    object.__setattr__(self, "_adapter", TypeAdapter(list[Any]))

  def encode(self, state: T | None = None) -> str:
    if self.state is None:
      if state is not None:
        raise ValueError(f"CustomId {self.prefix!r} carries no state.")
      return self.prefix
    if state is None:
      raise ValueError(f"CustomId {self.prefix!r} needs state.")
    dumped = state.model_dump(mode="json")
    values = [dumped[name] for name in self._fields]
    while values and values[-1] is None and self._optional(len(values) - 1):
      values.pop()
    encoded = (
      f"{self.prefix}:{json.dumps(values, separators=(',', ':'), ensure_ascii=False)}"
    )
    if len(encoded) > CUSTOM_ID_LIMIT:
      raise ValueError(
        f"custom_id for {self.prefix!r} is {len(encoded)} characters; Discord allows 100."
      )
    return encoded

  def decode(self, custom_id: str) -> T | None:
    prefix, separator, payload = custom_id.partition(":")
    if prefix != self.prefix:
      raise ValueError(f"custom_id {custom_id!r} does not belong to {self.prefix!r}.")
    if self.state is None:
      return None
    values = self._adapter.validate_json(payload) if separator else []
    return self.state.model_validate(dict(zip(self._fields, values)))

  def match(self, custom_id: str) -> dict[str, Any] | None:
    """A custom ID belongs to this one when its part before the first ':' is the prefix."""
    return {} if custom_id.partition(":")[0] == self.prefix else None

  def dump(self) -> JsonValue:
    return {
      "prefix": self.prefix
    }  # the router routes by prefix; state is decoded by the service

  @classmethod
  def load(cls, data: JsonValue) -> Self:
    if not isinstance(data, dict):
      raise TypeError("A custom ID route is an object.")
    return cls(str(data.get("prefix", "")))

  def _optional(self, index: int) -> bool:
    assert self.state is not None
    return not self.state.model_fields[self._fields[index]].is_required()
