import hashlib
import inspect
import json
from collections.abc import Awaitable, Callable
from json import JSONDecodeError
from re import fullmatch
from typing import Any

from jsonschema import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from ._event import EventSchema, JsonValue

type EventHandler[T] = Callable[[T], Awaitable[None]]

_SERVICE_NAME_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
_STANDARD_PATHS = frozenset(
  ("/health/drained", "/health/live", "/health/ready", "/schema")
)


class DuplicateEventHandlerError(ValueError):
  pass


class DuplicateEndpointError(ValueError):
  pass


class Service:
  def __init__(self, name: str) -> None:
    if fullmatch(_SERVICE_NAME_PATTERN, name) is None:
      raise ValueError(
        "Service names must contain only letters, numbers, dots, underscores, and "
        "hyphens, and must start and end with a letter or number."
      )
    self.name = name
    self._accepting = True
    self._sealed = False
    self._events: dict[str, tuple[EventSchema[Any], EventHandler[Any]]] = {}
    self._paths: set[str] = set(_STANDARD_PATHS)
    self._app = Starlette(
      routes=[
        Route("/health/live", self._live, methods=["GET"]),
        Route("/health/ready", self._ready, methods=["GET"]),
        Route("/health/drained", self._drained, methods=["GET"]),
        Route("/schema", self._schema, methods=["GET"]),
      ]
    )

  def listen[T](
    self,
    event: EventSchema[T],
  ) -> Callable[[EventHandler[T]], EventHandler[T]]:
    def register(handler: EventHandler[T]) -> EventHandler[T]:
      if self._sealed:
        raise RuntimeError("Event handlers cannot be added after the service starts.")
      if event.id in self._events:
        raise DuplicateEventHandlerError(
          f"Service {self.name!r} already handles event {event.id!r}."
        )
      if event.endpoint in self._paths:
        raise DuplicateEndpointError(
          f"Service {self.name!r} already has an endpoint at {event.endpoint!r}."
        )
      if not inspect.iscoroutinefunction(handler):
        raise TypeError("Event handlers must be async functions.")

      self._events[event.id] = (event, handler)
      self._paths.add(event.endpoint)
      self._app.add_route(
        event.endpoint,
        self._event_endpoint(event, handler),
        methods=["POST"],
        name=f"event:{event.id}",
      )
      return handler

    return register

  def drain(self) -> None:
    self._accepting = False

  def resume(self) -> None:
    self._accepting = True

  def dynamic_schema(self, *, root_path: str = "") -> dict[str, JsonValue]:
    normalized_root = self._root_path(root_path)
    schema = self._schema_document(normalized_root)
    schema["implementation_hash"] = self._implementation_hash()
    return schema

  def _schema_document(self, root_path: str) -> dict[str, JsonValue]:
    events: list[JsonValue] = []
    for event, handler in self._events.values():
      document = event.document()
      document["path"] = f"{root_path}{event.endpoint}"
      document["handler"] = f"{handler.__module__}:{handler.__qualname__}"
      events.append(document)
    events.sort(key=lambda value: str(value["id"]) if isinstance(value, dict) else "")

    return {
      "format": 1,
      "service": self.name,
      "asgi": {
        "root_path": root_path,
        "standard_endpoints": {
          "schema": f"{root_path}/schema",
          "live": f"{root_path}/health/live",
          "ready": f"{root_path}/health/ready",
          "drained": f"{root_path}/health/drained",
        },
      },
      "events": events,
    }

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    self._sealed = True
    await self._app(scope, receive, send)

  def _event_endpoint[T](
    self,
    event: EventSchema[T],
    handler: EventHandler[T],
  ) -> Callable[[Request], Awaitable[Response]]:
    async def endpoint(request: Request) -> Response:
      if not self._accepting:
        return JSONResponse({"detail": "Service is draining."}, status_code=503)
      content_type = request.headers.get("content-type", "").partition(";")[0].strip()
      if content_type != "application/json":
        return JSONResponse(
          {"detail": "Event requests require application/json."},
          status_code=415,
        )
      try:
        value: JsonValue = await request.json()
      except JSONDecodeError, UnicodeDecodeError:
        return JSONResponse(
          {"detail": "Request body is not valid JSON."}, status_code=400
        )
      try:
        event.validate(value)
        decoded = event.decode(value)
      except ValidationError as exc:
        return JSONResponse(
          {
            "detail": "Event payload does not match its schema.",
            "path": list(exc.absolute_path),
            "message": exc.message,
          },
          status_code=422,
        )
      except (TypeError, ValueError) as exc:
        return JSONResponse(
          {"detail": "Event payload could not be decoded.", "message": str(exc)},
          status_code=422,
        )
      await handler(decoded)
      return Response(status_code=204)

    return endpoint

  async def _live(self, request: Request) -> Response:
    return Response(status_code=204)

  async def _ready(self, request: Request) -> Response:
    return Response(status_code=204 if self._accepting else 503)

  async def _drained(self, request: Request) -> Response:
    return Response(status_code=204 if not self._accepting else 503)

  async def _schema(self, request: Request) -> Response:
    return JSONResponse(
      self.dynamic_schema(root_path=request.scope.get("root_path", ""))
    )

  @staticmethod
  def _root_path(value: str) -> str:
    if not value or value == "/":
      return ""
    if not value.startswith("/") or value.startswith("//"):
      raise ValueError("root_path must be an absolute URL path.")
    return value.rstrip("/")

  def _implementation_hash(self) -> str:
    encoded = json.dumps(
      self._schema_document(""),
      ensure_ascii=False,
      separators=(",", ":"),
      sort_keys=True,
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
