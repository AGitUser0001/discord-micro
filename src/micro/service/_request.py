from copy import deepcopy
from dataclasses import dataclass, field
from re import fullmatch
from typing import Any, cast

from pydantic import TypeAdapter

from ._event import JsonValue

_REQUEST_ID_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


@dataclass(frozen=True, slots=True)
class RequestSchema[InputT, OutputT]:
  id: str
  input: Any
  output: Any
  path: str | None = None
  _input_adapter: TypeAdapter[InputT] = field(init=False, repr=False, compare=False)
  _output_adapter: TypeAdapter[OutputT] = field(init=False, repr=False, compare=False)
  _input_schema: dict[str, JsonValue] = field(init=False, repr=False, compare=False)
  _output_schema: dict[str, JsonValue] = field(init=False, repr=False, compare=False)

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

    input_adapter = TypeAdapter[InputT](self.input)
    output_adapter = TypeAdapter[OutputT](self.output)
    object.__setattr__(self, "_input_adapter", input_adapter)
    object.__setattr__(self, "_output_adapter", output_adapter)
    object.__setattr__(
      self,
      "_input_schema",
      cast(dict[str, JsonValue], input_adapter.json_schema(mode="validation")),
    )
    object.__setattr__(
      self,
      "_output_schema",
      cast(dict[str, JsonValue], output_adapter.json_schema(mode="serialization")),
    )

  @property
  def endpoint(self) -> str:
    return self.path or f"/requests/{self.id}"

  def decode(self, value: JsonValue) -> InputT:
    return self._input_adapter.validate_python(value)

  def decode_json(self, value: bytes) -> InputT:
    return self._input_adapter.validate_json(value)

  def encode_input(self, value: InputT) -> JsonValue:
    validated = self._input_adapter.validate_python(value)
    return cast(JsonValue, self._input_adapter.dump_python(validated, mode="json"))

  def encode_input_json(self, value: InputT) -> bytes:
    validated = self._input_adapter.validate_python(value)
    return self._input_adapter.dump_json(validated)

  def decode_output(self, value: JsonValue) -> OutputT:
    return self._output_adapter.validate_python(value)

  def decode_output_json(self, value: bytes) -> OutputT:
    return self._output_adapter.validate_json(value)

  def encode(self, value: OutputT) -> JsonValue:
    validated = self._output_adapter.validate_python(value)
    return cast(JsonValue, self._output_adapter.dump_python(validated, mode="json"))

  def encode_json(self, value: OutputT) -> bytes:
    validated = self._output_adapter.validate_python(value)
    return self._output_adapter.dump_json(validated)

  def document(self) -> dict[str, JsonValue]:
    return {
      "id": self.id,
      "path": self.endpoint,
      "input": deepcopy(self._input_schema),
      "output": deepcopy(self._output_schema),
    }
