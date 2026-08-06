from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from re import fullmatch
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator

from ._event import EventScope, JsonSchema, JsonValue

_REQUEST_ID_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


def _identity(value: Any) -> Any:
  return value


@dataclass(frozen=True, slots=True)
class RequestSchema[InputT, OutputT]:
  id: str
  input: JsonSchema
  output: JsonSchema
  scope: EventScope = field(default_factory=EventScope)
  path: str | None = None
  decoder: Callable[[JsonValue], InputT] = _identity
  encoder: Callable[[OutputT], JsonValue] = _identity
  _input_validator: Validator = field(init=False, repr=False, compare=False)
  _output_validator: Validator = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    if fullmatch(_REQUEST_ID_PATTERN, self.id) is None:
      raise ValueError(
        "Request schema IDs must contain only letters, numbers, dots, underscores, "
        "and hyphens, and must start and end with a letter or number."
      )
    if self.path is not None and (
      not self.path.startswith("/") or self.path.startswith("//")
    ):
      raise ValueError("Custom request paths must be absolute URL paths.")

    input_schema = _copy_schema(self.input)
    output_schema = _copy_schema(self.output)
    Draft202012Validator.check_schema(input_schema)
    Draft202012Validator.check_schema(output_schema)
    object.__setattr__(self, "input", _freeze_schema(input_schema))
    object.__setattr__(self, "output", _freeze_schema(output_schema))
    object.__setattr__(self, "_input_validator", Draft202012Validator(input_schema))
    object.__setattr__(self, "_output_validator", Draft202012Validator(output_schema))

  @property
  def endpoint(self) -> str:
    return self.path or f"/requests/{self.id}"

  def decode(self, value: JsonValue) -> InputT:
    self.validate_input(value)
    return self.decoder(value)

  def encode(self, value: OutputT) -> JsonValue:
    encoded = self.encoder(value)
    self.validate_output(encoded)
    return encoded

  def validate_input(self, value: JsonValue) -> None:
    self._input_validator.validate(value)

  def validate_output(self, value: JsonValue) -> None:
    self._output_validator.validate(value)

  def document(self) -> dict[str, JsonValue]:
    return {
      "id": self.id,
      "path": self.endpoint,
      "scope": self.scope.document(),
      "input": _copy_schema(self.input),
      "output": _copy_schema(self.output),
    }


def _copy_schema(schema: JsonSchema) -> bool | dict[str, JsonValue]:
  return deepcopy(dict(schema) if isinstance(schema, Mapping) else schema)


def _freeze_schema(schema: JsonSchema) -> JsonSchema:
  return MappingProxyType(schema) if isinstance(schema, dict) else schema
