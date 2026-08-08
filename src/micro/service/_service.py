import inspect
from collections.abc import Awaitable, Callable
from re import fullmatch
from typing import Any

from pydantic import JsonValue, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from micro._microservices import (
  GatewayClient,
  Microservice,
  MicroserviceClient,
  StateReceiver,
  StoreClient,
)
from micro.queue import QueueClient

from ._client import ServiceClient
from ._event import EventSchema
from ._request import RequestSchema

type EventHandler[T] = Callable[[T], Awaitable[None]]
type RequestHandler[InputT, OutputT] = Callable[[InputT], Awaitable[OutputT]]

_SERVICE_NAME_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


class DuplicateEventHandlerError(ValueError):
  pass


class DuplicateRequestHandlerError(ValueError):
  pass


class Service(Microservice):
  """Application microservice implementing typed events and requests."""

  def __init__(
    self,
    name: str,
    *,
    state_receiver: StateReceiver | None = None,
  ) -> None:
    if fullmatch(_SERVICE_NAME_PATTERN, name) is None:
      raise ValueError(
        "Service names must contain only letters, numbers, dots, underscores, and "
        "hyphens, and must start and end with a letter or number."
      )
    self.client = ServiceClient()
    self.store = StoreClient()
    self.gateway = GatewayClient()
    self.queue = QueueClient()
    receivers: tuple[StateReceiver, ...] = (
      self.client,
      self.store,
      self.gateway,
      self.queue,
      *((state_receiver,) if state_receiver is not None else ()),
    )
    super().__init__("service", state_receiver=_StateReceivers(receivers))
    self.name = name
    self._events: dict[str, tuple[EventSchema[Any], EventHandler[Any]]] = {}
    self._requests: dict[
      str, tuple[RequestSchema[Any, Any], RequestHandler[Any, Any]]
    ] = {}

  async def close(self) -> None:
    await self.client.aclose()
    await self.store.aclose()
    await self.gateway.aclose()
    await self.queue.aclose()

  def listen[T](
    self,
    event: EventSchema[T],
  ) -> Callable[[EventHandler[T]], EventHandler[T]]:
    def register(handler: EventHandler[T]) -> EventHandler[T]:
      if self._sealed:
        raise RuntimeError("Event handlers cannot be added after the service starts.")
      if event.id in self._events:
        raise DuplicateEventHandlerError(
          f"This service already handles event {event.id!r}."
        )
      if not inspect.iscoroutinefunction(handler):
        raise TypeError("Event handlers must be async functions.")
      self.add_route(
        event.endpoint,
        self._event_endpoint(event, handler),
        methods=("POST",),
        name=f"event:{event.id}",
      )
      self._events[event.id] = (event, handler)
      return handler

    return register

  def handle[InputT, OutputT](
    self,
    request: RequestSchema[InputT, OutputT],
  ) -> Callable[[RequestHandler[InputT, OutputT]], RequestHandler[InputT, OutputT]]:
    def register(
      handler: RequestHandler[InputT, OutputT],
    ) -> RequestHandler[InputT, OutputT]:
      if self._sealed:
        raise RuntimeError("Request handlers cannot be added after the service starts.")
      if request.id in self._requests:
        raise DuplicateRequestHandlerError(
          f"This service already handles request {request.id!r}."
        )
      if not inspect.iscoroutinefunction(handler):
        raise TypeError("Request handlers must be async functions.")
      self.add_route(
        request.endpoint,
        self._request_endpoint(request, handler),
        methods=("POST",),
        name=f"request:{request.id}",
      )
      self._requests[request.id] = (request, handler)
      return handler

    return register

  def schema_document(self, root_path: str) -> dict[str, JsonValue]:
    document = super().schema_document(root_path)
    document["service"] = self.name
    events: list[JsonValue] = []
    for event, handler in self._events.values():
      operation = event.document()
      operation["path"] = f"{root_path}{event.endpoint}"
      operation["handler"] = f"{handler.__module__}:{handler.__qualname__}"
      events.append(operation)
    events.sort(key=lambda value: str(value["id"]) if isinstance(value, dict) else "")
    requests: list[JsonValue] = []
    for request, handler in self._requests.values():
      operation = request.document()
      operation["path"] = f"{root_path}{request.endpoint}"
      operation["handler"] = f"{handler.__module__}:{handler.__qualname__}"
      requests.append(operation)
    requests.sort(key=lambda value: str(value["id"]) if isinstance(value, dict) else "")
    document["events"] = events
    document["requests"] = requests
    return document

  def _event_endpoint[T](
    self,
    event: EventSchema[T],
    handler: EventHandler[T],
  ) -> Callable[[Request], Awaitable[Response]]:
    async def endpoint(request: Request) -> Response:
      if not self.accepting:
        return JSONResponse({"detail": "Service is draining."}, status_code=503)
      if _content_type(request) != "application/json":
        return JSONResponse(
          {"detail": "Event requests require application/json."}, status_code=415
        )
      try:
        decoded = event.decode_json(await request.body())
      except ValidationError as exc:
        return _validation_error(exc, "Event payload")
      except (TypeError, ValueError) as exc:
        return JSONResponse(
          {"detail": "Event payload could not be decoded.", "message": str(exc)},
          status_code=422,
        )
      await handler(decoded)
      return Response(status_code=204)

    return endpoint

  def _request_endpoint[InputT, OutputT](
    self,
    request_schema: RequestSchema[InputT, OutputT],
    handler: RequestHandler[InputT, OutputT],
  ) -> Callable[[Request], Awaitable[Response]]:
    async def endpoint(request: Request) -> Response:
      if not self.accepting:
        return JSONResponse({"detail": "Service is draining."}, status_code=503)
      if _content_type(request) != "application/json":
        return JSONResponse(
          {"detail": "Requests require application/json."}, status_code=415
        )
      try:
        decoded = request_schema.decode_json(await request.body())
      except ValidationError as exc:
        return _validation_error(exc, "Request input")
      except (TypeError, ValueError) as exc:
        return JSONResponse(
          {"detail": "Request input could not be decoded.", "message": str(exc)},
          status_code=422,
        )
      result = await handler(decoded)
      try:
        encoded = request_schema.encode_json(result)
      except ValidationError, TypeError, ValueError:
        return JSONResponse(
          {"detail": "Handler output does not match its schema."}, status_code=500
        )
      return Response(encoded, media_type="application/json")

    return endpoint


def _content_type(request: Request) -> str:
  return request.headers.get("content-type", "").partition(";")[0].strip()


class _StateReceivers:
  def __init__(self, receivers: tuple[StateReceiver, ...]) -> None:
    self._receivers = receivers

  def apply_state(self, state: JsonValue) -> None:
    snapshots = {
      receiver: receiver._state_snapshot()
      for receiver in self._receivers
      if isinstance(receiver, MicroserviceClient)
    }
    try:
      for receiver in self._receivers:
        receiver.apply_state(state)
    except Exception:
      for receiver, snapshot in snapshots.items():
        receiver._restore_state(snapshot)
      raise


def _validation_error(exc: ValidationError, subject: str) -> JSONResponse:
  error = exc.errors(include_url=False)[0]
  if error["type"] == "json_invalid":
    return JSONResponse({"detail": "Request body is not valid JSON."}, status_code=400)
  return JSONResponse(
    {
      "detail": f"{subject} does not match its schema.",
      "path": list(error["loc"]),
      "message": error["msg"],
    },
    status_code=422,
  )
