from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Self
from urllib.parse import urlsplit

import httpx2

from micro.service import EventSchema, JsonValue, RequestSchema

type ServiceSchema = Mapping[str, Any]
type ServiceRegistration = tuple[str, str, ServiceSchema]


class InvalidServiceSchemaError(ValueError):
  pass


class NoCompatibleInstanceError(LookupError):
  pass


class RemoteServiceError(RuntimeError):
  def __init__(self, instance_id: str, status_code: int, body: str) -> None:
    self.instance_id = instance_id
    self.status_code = status_code
    self.body = body
    super().__init__(
      f"Service instance {instance_id!r} returned HTTP {status_code}: {body}"
    )


class StaleStateError(ValueError):
  pass


@dataclass(frozen=True, slots=True)
class _Instance:
  id: str
  base_url: str
  schema: dict[str, Any]


class ServiceClient:
  def __init__(
    self,
    registrations: Iterable[ServiceRegistration] = (),
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
  ) -> None:
    self._instances: dict[str, _Instance] = {}
    self._positions: dict[tuple[str, str], int] = {}
    self._state_revision = -1
    self._http = httpx2.AsyncClient(transport=transport, timeout=timeout)
    for instance_id, base_url, schema in registrations:
      self.add(instance_id, base_url, schema)

  def add(self, instance_id: str, base_url: str, schema: ServiceSchema) -> None:
    instance = _make_instance(instance_id, base_url, schema)
    self._instances[instance_id] = instance

  def remove(self, instance_id: str) -> bool:
    return self._instances.pop(instance_id, None) is not None

  def clear(self) -> None:
    self._instances.clear()
    self._positions.clear()

  def apply_state(self, state: JsonValue) -> None:
    if not isinstance(state, dict):
      raise TypeError("Overseer state must be an object.")
    revision = state.get("revision")
    registrations = state.get("instances")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
      raise ValueError("Overseer state needs a non-negative integer revision.")
    if not isinstance(registrations, list):
      raise TypeError("Overseer state needs an instances list.")
    if revision < self._state_revision:
      raise StaleStateError(
        f"State revision {revision} is older than {self._state_revision}."
      )
    if revision == self._state_revision:
      return

    replacement: dict[str, _Instance] = {}
    for registration in registrations:
      if not isinstance(registration, dict):
        raise TypeError("Every instance registration must be an object.")
      instance_id = registration.get("id")
      base_url = registration.get("base_url")
      schema = registration.get("schema")
      if not isinstance(instance_id, str) or not isinstance(base_url, str):
        raise TypeError("Every instance needs string id and base_url fields.")
      if not isinstance(schema, dict):
        raise TypeError("Every instance needs a service schema object.")
      if instance_id in replacement:
        raise ValueError(f"Duplicate instance ID {instance_id!r}.")
      replacement[instance_id] = _make_instance(instance_id, base_url, schema)

    self._instances = replacement
    self._positions.clear()
    self._state_revision = revision

  @property
  def instance_ids(self) -> tuple[str, ...]:
    return tuple(self._instances)

  @property
  def state_revision(self) -> int:
    return self._state_revision

  async def emit[T](self, event: EventSchema[T], payload: T) -> None:
    encoded = event.encode(payload)
    instance, endpoint = self._select("events", event.id, event.document())
    response = await self._http.post(f"{instance.base_url}{endpoint}", json=encoded)
    if not response.is_success:
      raise RemoteServiceError(instance.id, response.status_code, response.text)

  async def request[InputT, OutputT](
    self,
    request: RequestSchema[InputT, OutputT],
    payload: InputT,
  ) -> OutputT:
    encoded = request.encode_input(payload)
    instance, endpoint = self._select("requests", request.id, request.document())
    response = await self._http.post(f"{instance.base_url}{endpoint}", json=encoded)
    if not response.is_success:
      raise RemoteServiceError(instance.id, response.status_code, response.text)
    value: JsonValue = response.json()
    return request.decode_output(value)

  async def aclose(self) -> None:
    await self._http.aclose()

  async def __aenter__(self) -> Self:
    return self

  async def __aexit__(self, *exc_info: object) -> None:
    await self.aclose()

  def _select(
    self,
    collection: str,
    operation_id: str,
    expected: Mapping[str, Any],
  ) -> tuple[_Instance, str]:
    candidates: list[tuple[_Instance, str]] = []
    for instance in self._instances.values():
      operations = instance.schema[collection]
      for operation in operations:
        if operation["id"] == operation_id and _compatible(
          collection, expected, operation
        ):
          candidates.append((instance, operation["path"]))
          break

    if not candidates:
      raise NoCompatibleInstanceError(
        f"No service instance advertises a compatible {collection[:-1]} "
        f"for {operation_id!r}."
      )

    key = (collection, operation_id)
    position = self._positions.get(key, 0)
    selected = candidates[position % len(candidates)]
    self._positions[key] = position + 1
    return selected


def _make_instance(instance_id: str, base_url: str, schema: ServiceSchema) -> _Instance:
  if not instance_id:
    raise ValueError("instance_id cannot be empty.")
  parsed_url = urlsplit(base_url)
  if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
    raise ValueError("base_url must be an absolute HTTP(S) URL.")
  if parsed_url.query or parsed_url.fragment:
    raise ValueError("base_url cannot contain a query or fragment.")

  return _Instance(instance_id, base_url.rstrip("/"), _validate_schema(schema))


def _validate_schema(schema: ServiceSchema) -> dict[str, Any]:
  document = deepcopy(dict(schema))
  if document.get("format") != 1:
    raise InvalidServiceSchemaError("Only service schema format 1 is supported.")
  if not isinstance(document.get("service"), str):
    raise InvalidServiceSchemaError("Service schema must contain a service name.")
  for collection in ("events", "requests"):
    operations = document.get(collection)
    if not isinstance(operations, list):
      raise InvalidServiceSchemaError(
        f"Service schema must contain a {collection} list."
      )
    for operation in operations:
      if not isinstance(operation, dict):
        raise InvalidServiceSchemaError(f"Every {collection} entry must be an object.")
      if not isinstance(operation.get("id"), str):
        raise InvalidServiceSchemaError(f"Every {collection} entry needs an ID.")
      path = operation.get("path")
      if not isinstance(path, str) or not path.startswith("/"):
        raise InvalidServiceSchemaError(
          f"Every {collection} entry needs an absolute path."
        )
  return document


def _compatible(
  collection: str,
  expected: Mapping[str, Any],
  advertised: Mapping[str, Any],
) -> bool:
  fields = (
    ("scope", "payload")
    if collection == "events"
    else (
      "scope",
      "input",
      "output",
    )
  )
  return all(expected.get(field) == advertised.get(field) for field in fields)
