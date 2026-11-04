from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import JsonValue, TypeAdapter

from micro import subjects

from ._event import schema_hash


@dataclass(frozen=True, slots=True)
class RequestSchema[InputT, OutputT]:
  """A typed request/reply operation. Exactly one replica answers each call."""

  id: str
  input: Any
  output: Any
  _input_adapter: TypeAdapter[InputT] = field(init=False, repr=False, compare=False)
  _output_adapter: TypeAdapter[OutputT] = field(init=False, repr=False, compare=False)
  _input_schema: dict[str, JsonValue] = field(init=False, repr=False, compare=False)
  _output_schema: dict[str, JsonValue] = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    try:
      subjects.dotted(self.id)
    except ValueError as exc:
      raise ValueError(
        "Request schema IDs must contain only letters, numbers, dots, underscores, "
        "and hyphens, and must start and end with a letter or number."
      ) from exc
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
  def subject(self) -> str:
    return subjects.request(self.id)

  @property
  def hash(self) -> str:
    """Identifies the input/output contract; callers and handlers compare it."""
    return schema_hash({"input": self._input_schema, "output": self._output_schema})

  def decode_input_json(self, value: bytes) -> InputT:
    return self._input_adapter.validate_json(value)

  def encode_input_json(self, value: InputT) -> bytes:
    return self._input_adapter.dump_json(self._input_adapter.validate_python(value))

  def decode_output_json(self, value: bytes) -> OutputT:
    return self._output_adapter.validate_json(value)

  def encode_output_json(self, value: OutputT) -> bytes:
    return self._output_adapter.dump_json(self._output_adapter.validate_python(value))

  def document(self) -> dict[str, JsonValue]:
    return {
      "id": self.id,
      "input": deepcopy(self._input_schema),
      "output": deepcopy(self._output_schema),
    }
