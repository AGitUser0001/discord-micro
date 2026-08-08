from copy import deepcopy
from dataclasses import dataclass, field
from re import fullmatch
from typing import Any, cast

from pydantic import JsonValue, TypeAdapter

type JsonSchema = bool | dict[str, JsonValue]

_EVENT_ID_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


@dataclass(frozen=True, slots=True)
class EventSchema[T]:
  id: str
  payload: Any
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

  def decode_json(self, value: bytes) -> T:
    return self._adapter.validate_json(value)

  def encode(self, value: T) -> JsonValue:
    validated = self._adapter.validate_python(value)
    return cast(JsonValue, self._adapter.dump_python(validated, mode="json"))

  def encode_json(self, value: T) -> bytes:
    validated = self._adapter.validate_python(value)
    return self._adapter.dump_json(validated)

  def document(self) -> dict[str, JsonValue]:
    return {
      "id": self.id,
      "path": self.endpoint,
      "payload": deepcopy(self._payload_schema),
    }
