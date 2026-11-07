import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import JsonValue, TypeAdapter

from micro import subjects


def schema_hash(document: JsonValue) -> str:
  encoded = json.dumps(document, separators=(",", ":"), sort_keys=True).encode()
  return hashlib.sha256(encoded).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class EventSchema[T]:
  """A typed application event. Every listening service receives each one once."""

  id: str
  payload: Any
  _adapter: TypeAdapter[T] = field(init=False, repr=False, compare=False)
  _payload_schema: dict[str, JsonValue] = field(init=False, repr=False, compare=False)

  def __post_init__(self) -> None:
    try:
      self._validate_id()
    except ValueError as exc:
      raise ValueError(
        "Event schema IDs must contain only letters, numbers, dots, underscores, "
        "and hyphens, and must start and end with a letter or number."
      ) from exc

  def _adapter_(self) -> TypeAdapter[T]:
    # Built on first use: creating validators for every Discord event up front
    # costs seconds and megabytes no listener asked for.
    try:
      return self._adapter
    except AttributeError:
      adapter = TypeAdapter[T](self.payload)
      object.__setattr__(self, "_adapter", adapter)
      return adapter

  def _schema(self) -> dict[str, JsonValue]:
    try:
      return self._payload_schema
    except AttributeError:
      schema = cast(
        dict[str, JsonValue], self._adapter_().json_schema(mode="validation")
      )
      object.__setattr__(self, "_payload_schema", schema)
      return schema

  def _validate_id(self) -> None:
    subjects.dotted(self.id)

  @property
  def subject(self) -> str:
    """The subject this event is published on."""
    return subjects.event(self.id)

  def listen_subject(self, *, guild_id: int | None = None) -> str:
    """The subject filter a listener subscribes to."""
    if guild_id is not None:
      raise ValueError(f"Event {self.id!r} is not scoped to guilds.")
    return subjects.event(self.id)

  def matches(self, subject: str) -> bool:
    """Whether a subject belongs to this event."""
    return subject == subjects.event(self.id)

  def decode_json(self, value: bytes) -> T:
    """Validate and decode an event payload."""
    return self._adapter_().validate_json(value)

  def encode_json(self, value: T) -> bytes:
    """Encode an event payload as JSON."""
    adapter = self._adapter_()
    return adapter.dump_json(adapter.validate_python(value))

  @property
  def hash(self) -> str:
    """Identifies the payload contract; replicas compare it during rolling updates."""
    return schema_hash(self._schema())

  def document(self) -> dict[str, JsonValue]:
    """The schema as a JSON document."""
    return {"id": self.id, "payload": deepcopy(self._schema())}


@dataclass(frozen=True, slots=True)
class DispatchSchema[T](EventSchema[T]):
  """A raw Discord Gateway dispatch, published only by the shard's owner."""

  def _validate_id(self) -> None:
    subjects.token(self.id)

  @property
  def subject(self) -> str:
    """The subject filter for every guild's dispatch of this event."""
    raise TypeError("Discord dispatches are published only by Gateway workers.")

  def listen_subject(self, *, guild_id: int | None = None) -> str:
    return subjects.dispatch_filter(self.id, "*" if guild_id is None else guild_id)

  def matches(self, subject: str) -> bool:
    """Whether a subject is a dispatch of this event."""
    prefix = subjects.dispatch_filter(self.id, "*")[:-1]
    return subject.startswith(prefix) and "." not in subject[len(prefix) :]
