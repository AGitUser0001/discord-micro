from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Self
from urllib.parse import urlsplit

import httpx2
from pydantic import JsonValue

type MicroserviceSchema = Mapping[str, Any]
type MicroserviceRegistration = tuple[str, str, MicroserviceSchema]


class InvalidMicroserviceSchemaError(ValueError):
  pass


class NoCompatibleInstanceError(LookupError):
  pass


class RemoteMicroserviceError(RuntimeError):
  def __init__(self, instance_id: str, status_code: int, body: str) -> None:
    self.instance_id = instance_id
    self.status_code = status_code
    self.body = body
    super().__init__(
      f"Microservice instance {instance_id!r} returned HTTP {status_code}: {body}"
    )


class StaleStateError(ValueError):
  pass


@dataclass(frozen=True, slots=True)
class Instance:
  id: str
  base_url: str
  schema: dict[str, Any]


class MicroserviceClient:
  """Revisioned, schema-aware routing shared by all Micro clients."""

  def __init__(
    self,
    registrations: Iterable[MicroserviceRegistration] = (),
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
  ) -> None:
    self._instances: dict[str, Instance] = {}
    self._positions: dict[str, int] = {}
    self._state_revision = -1
    self._http = httpx2.AsyncClient(transport=transport, timeout=timeout)
    for instance_id, base_url, schema in registrations:
      self.add(instance_id, base_url, schema)

  def add(self, instance_id: str, base_url: str, schema: MicroserviceSchema) -> None:
    self._instances[instance_id] = self.make_instance(instance_id, base_url, schema)

  def remove(self, instance_id: str) -> bool:
    return self._instances.pop(instance_id, None) is not None

  def clear(self) -> None:
    self._instances.clear()
    self._positions.clear()

  def apply_state(self, state: JsonValue) -> None:
    if not isinstance(state, dict):
      raise TypeError("Overseer state must be an object.")
    schemas = state.get("schemas")
    if not isinstance(schemas, dict):
      raise TypeError("Overseer state needs a schemas object.")
    validated: dict[str, dict[str, Any]] = {}
    for schema_hash, schema in schemas.items():
      if not isinstance(schema_hash, str) or not isinstance(schema, dict):
        raise TypeError("Every schema entry needs a string hash and object value.")
      validated[schema_hash] = self.validate_schema(schema)

    def registration(value: dict[str, JsonValue]) -> Instance:
      schema_hash = value.get("schema")
      if not isinstance(schema_hash, str):
        raise TypeError("Every service instance needs a string schema hash.")
      try:
        schema = validated[schema_hash]
      except KeyError as exc:
        raise ValueError(
          f"Service instance references unknown schema {schema_hash!r}."
        ) from exc
      return self._instance_registration(value, schema)

    self._apply_state_collection(state, "instances", registration)

  def _apply_state_collection(
    self,
    state: JsonValue,
    collection: str,
    parse_registration: Callable[[dict[str, JsonValue]], Instance],
  ) -> None:
    if not isinstance(state, dict):
      raise TypeError("Overseer state must be an object.")
    revision = state.get("revision")
    registrations = state.get(collection, [])
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
      raise ValueError("Overseer state needs a non-negative integer revision.")
    if not isinstance(registrations, list):
      raise TypeError(f"Overseer state needs a {collection} list.")
    if revision < self._state_revision:
      raise StaleStateError(
        f"State revision {revision} is older than {self._state_revision}."
      )
    if revision == self._state_revision:
      return

    replacement: dict[str, Instance] = {}
    for registration in registrations:
      if not isinstance(registration, dict):
        raise TypeError("Every instance registration must be an object.")
      instance = parse_registration(registration)
      if instance.id in replacement:
        raise ValueError(f"Duplicate instance ID {instance.id!r}.")
      replacement[instance.id] = instance

    self._instances = replacement
    self._positions.clear()
    self._state_revision = revision

  def _instance_registration(
    self,
    registration: dict[str, JsonValue],
    schema: dict[str, Any],
  ) -> Instance:
    instance_id = registration.get("id")
    base_url = registration.get("base_url")
    if not isinstance(instance_id, str) or not isinstance(base_url, str):
      raise TypeError("Every instance needs string id and base_url fields.")
    return self.make_instance(instance_id, base_url, schema, validate=False)

  @property
  def instance_ids(self) -> tuple[str, ...]:
    return tuple(self._instances)

  @property
  def state_revision(self) -> int:
    return self._state_revision

  def _state_snapshot(
    self,
  ) -> tuple[dict[str, Instance], dict[str, int], int]:
    return dict(self._instances), dict(self._positions), self._state_revision

  def _restore_state(
    self,
    snapshot: tuple[dict[str, Instance], dict[str, int], int],
  ) -> None:
    self._instances, self._positions, self._state_revision = snapshot

  async def post(
    self,
    instance: Instance,
    path: str,
    body: bytes,
    *,
    content_type: str = "application/json",
    headers: Mapping[str, str] | None = None,
  ) -> bytes:
    request_headers = {"content-type": content_type}
    if headers is not None:
      request_headers.update(headers)
    response = await self._http.post(
      f"{instance.base_url}{path}",
      content=body,
      headers=request_headers,
    )
    if not response.is_success:
      raise RemoteMicroserviceError(instance.id, response.status_code, response.text)
    return response.content

  def select(self, key: str, candidates: list[Instance]) -> Instance:
    if not candidates:
      raise NoCompatibleInstanceError(
        f"No microservice instance is compatible with {key!r}."
      )
    position = self._positions.get(key, 0)
    selected = candidates[position % len(candidates)]
    self._positions[key] = position + 1
    return selected

  async def aclose(self) -> None:
    await self._http.aclose()

  async def __aenter__(self) -> Self:
    return self

  async def __aexit__(self, *exc_info: object) -> None:
    await self.aclose()

  def validate_schema(self, schema: MicroserviceSchema) -> dict[str, Any]:
    document = deepcopy(dict(schema))
    if document.get("format") != 1:
      raise InvalidMicroserviceSchemaError(
        "Only microservice schema format 1 is supported."
      )
    if not isinstance(document.get("kind"), str):
      raise InvalidMicroserviceSchemaError("Microservice schema must contain a kind.")
    return document

  def make_instance(
    self,
    instance_id: str,
    base_url: str,
    schema: MicroserviceSchema,
    *,
    validate: bool = True,
  ) -> Instance:
    if not instance_id:
      raise ValueError("instance_id cannot be empty.")
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
      raise ValueError("base_url must be an absolute HTTP(S) URL.")
    if parsed_url.query or parsed_url.fragment:
      raise ValueError("base_url cannot contain a query or fragment.")
    document = self.validate_schema(schema) if validate else schema
    if not isinstance(document, dict):
      raise TypeError("Validated microservice schemas must be dictionaries.")
    return Instance(instance_id, base_url.rstrip("/"), document)
