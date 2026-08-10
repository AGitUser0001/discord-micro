import asyncio
from collections.abc import Iterable, Mapping
from typing import Any

import httpx2

from micro._microservices import (
  Instance,
  InvalidMicroserviceSchemaError,
  MicroserviceClient,
  MicroserviceSchema,
  NoCompatibleInstanceError,
)

from ._event import EventSchema
from ._request import RequestSchema

type ServiceSchema = Mapping[str, Any]
type ServiceRegistration = tuple[str, str, ServiceSchema]


class ServiceClient(MicroserviceClient):
  def __init__(
    self,
    registrations: Iterable[ServiceRegistration] = (),
    *,
    transport: httpx2.AsyncBaseTransport | None = None,
    timeout: float = 5.0,
    max_concurrency: int = 100,
  ) -> None:
    if max_concurrency <= 0:
      raise ValueError("max_concurrency must be positive.")
    self._concurrency = asyncio.Semaphore(max_concurrency)
    super().__init__(
      (
        (instance_id, base_url, schema)
        for instance_id, base_url, schema in registrations
      ),
      transport=transport,
      timeout=timeout,
    )

  async def emit[T](self, event: EventSchema[T], payload: T) -> None:
    instance, endpoint = self._select("events", event.id, event.document())
    await self.post(instance, endpoint, event.encode_json(payload))

  async def request[InputT, OutputT](
    self,
    request: RequestSchema[InputT, OutputT],
    payload: InputT,
  ) -> OutputT:
    instance, endpoint = self._select("requests", request.id, request.document())
    content = await self.post(instance, endpoint, request.encode_input_json(payload))
    return request.decode_output_json(content)

  async def route_event(self, event_id: str, payload: bytes) -> int:
    """Deliver raw event JSON once to each logical service that listens for it."""
    candidates: dict[str, list[tuple[Instance, str]]] = {}
    for instance in self._instances.values():
      for operation in instance.schema["events"]:
        if operation["id"] == event_id:
          service = instance.schema["service"]
          candidates.setdefault(service, []).append((instance, operation["path"]))
          break
    selected = [
      group[self._positions.get(f"event-route:{event_id}:{service}", 0) % len(group)]
      for service, group in candidates.items()
    ]
    for service in candidates:
      key = f"event-route:{event_id}:{service}"
      self._positions[key] = self._positions.get(key, 0) + 1

    async def deliver(instance: Instance, path: str) -> None:
      async with self._concurrency:
        await self.post(instance, path, payload)

    await asyncio.gather(*(deliver(instance, path) for instance, path in selected))
    return len(selected)

  def validate_schema(self, schema: MicroserviceSchema) -> dict[str, Any]:
    document = super().validate_schema(schema)
    if document.get("kind") != "service":
      raise InvalidMicroserviceSchemaError("Schema does not describe a service.")
    if not isinstance(document.get("service"), str) or not document["service"]:
      raise InvalidMicroserviceSchemaError(
        "Service schema must contain a non-empty service name."
      )
    for collection in ("events", "requests"):
      operations = document.get(collection)
      if not isinstance(operations, list):
        raise InvalidMicroserviceSchemaError(
          f"Service schema must contain a {collection} list."
        )
      for operation in operations:
        if not isinstance(operation, dict):
          raise InvalidMicroserviceSchemaError(
            f"Every {collection} entry must be an object."
          )
        if not isinstance(operation.get("id"), str):
          raise InvalidMicroserviceSchemaError(f"Every {collection} entry needs an ID.")
        path = operation.get("path")
        if not isinstance(path, str) or not path.startswith("/"):
          raise InvalidMicroserviceSchemaError(
            f"Every {collection} entry needs an absolute path."
          )
    return document

  def _select(
    self,
    collection: str,
    operation_id: str,
    expected: Mapping[str, Any],
  ) -> tuple[Instance, str]:
    candidates: list[Instance] = []
    paths: dict[str, str] = {}
    for instance in self._instances.values():
      for operation in instance.schema[collection]:
        if operation["id"] == operation_id and _compatible(
          collection, expected, operation
        ):
          candidates.append(instance)
          paths[instance.id] = operation["path"]
          break
    try:
      instance = self.select(f"{collection}:{operation_id}", candidates)
    except NoCompatibleInstanceError as exc:
      raise NoCompatibleInstanceError(
        f"No service instance advertises a compatible {collection[:-1]} "
        f"for {operation_id!r}."
      ) from exc
    return instance, paths[instance.id]


def _compatible(
  collection: str,
  expected: Mapping[str, Any],
  advertised: Mapping[str, Any],
) -> bool:
  fields = ("payload",) if collection == "events" else ("input", "output")
  return all(expected.get(field) == advertised.get(field) for field in fields)
