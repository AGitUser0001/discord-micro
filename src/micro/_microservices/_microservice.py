import hashlib
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import Any

from pydantic import JsonValue
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

type Endpoint = Callable[[Request], Awaitable[Response]]

_STANDARD_PATHS = frozenset(
  ("/health/drained", "/health/live", "/health/ready", "/schema", "/state")
)


def request_content_type(request: Request) -> str:
  return request.headers.get("content-type", "").partition(";")[0].strip()


class DuplicateEndpointError(ValueError):
  pass


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
  component: str
  event: str
  attributes: dict[str, Any] = field(default_factory=dict)


type EventObserver = Callable[[LifecycleEvent], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class OperationEvent:
  """A framework operation transition suitable for metrics and tracing."""

  component: str
  operation: str
  phase: str
  attributes: dict[str, Any] = field(default_factory=dict)


type OperationObserver = Callable[[OperationEvent], Awaitable[None]]


class Microservice:
  """Shared ASGI and lifecycle machinery for every networked Micro worker."""

  def __init__(
    self,
    kind: str,
  ) -> None:
    if not kind:
      raise ValueError("Microservice kind cannot be empty.")
    self.kind = kind
    self._accepting = True
    self._running = False
    self._sealed = False
    self._paths: set[str] = set(_STANDARD_PATHS)
    self._observers: list[EventObserver] = []
    self._operation_observers: list[OperationObserver] = []
    self._app = Starlette(
      lifespan=self._lifespan,
      routes=[
        Route("/health/live", self._live_endpoint, methods=["GET"]),
        Route("/health/ready", self._ready_endpoint, methods=["GET"]),
        Route("/health/drained", self._drained_endpoint, methods=["GET"]),
        Route("/schema", self._schema_endpoint, methods=["GET"]),
        Route("/state", self._state_endpoint, methods=["POST"]),
      ],
    )

  def add_route(
    self,
    path: str,
    endpoint: Endpoint,
    *,
    methods: tuple[str, ...],
    name: str | None = None,
  ) -> None:
    if self._sealed:
      raise RuntimeError("Endpoints cannot be added after the microservice starts.")
    if not path.startswith("/") or path.startswith("//"):
      raise ValueError("Endpoint paths must be absolute URL paths.")
    if path in self._paths:
      raise DuplicateEndpointError(
        f"Microservice {self.kind!r} already has an endpoint at {path!r}."
      )
    self._paths.add(path)
    self._app.add_route(path, endpoint, methods=list(methods), name=name)

  def drain(self) -> None:
    self._accepting = False

  def add_observer(self, observer: EventObserver) -> None:
    self._observers.append(observer)

  def add_operation_observer(self, observer: OperationObserver) -> None:
    self._operation_observers.append(observer)

  @asynccontextmanager
  async def operation(self, name: str, **attributes: Any) -> AsyncIterator[None]:
    """Emit structured start/completion/failure transitions around an operation."""
    await self._emit_operation(name, "started", attributes)
    try:
      yield
    except BaseException as exc:
      await self._emit_operation(name, "failed", attributes | {"error": str(exc)})
      raise
    else:
      await self._emit_operation(name, "completed", attributes)

  def resume(self) -> None:
    self._accepting = True

  @property
  def accepting(self) -> bool:
    return self._accepting

  @property
  def running(self) -> bool:
    return self._running

  @property
  def ready(self) -> bool:
    return self._running and self._accepting and self.component_ready

  @property
  def component_ready(self) -> bool:
    return True

  def dynamic_schema(self, *, root_path: str = "") -> dict[str, JsonValue]:
    normalized_root = self._root_path(root_path)
    document = self.schema_document(normalized_root)
    document["implementation_hash"] = self._implementation_hash()
    return document

  def schema_document(self, root_path: str) -> dict[str, JsonValue]:
    return {
      "format": 1,
      "kind": self.kind,
      "asgi": {
        "root_path": root_path,
        "standard_endpoints": {
          "schema": f"{root_path}/schema",
          "live": f"{root_path}/health/live",
          "ready": f"{root_path}/health/ready",
          "drained": f"{root_path}/health/drained",
          "state": f"{root_path}/state",
        },
      },
    }

  async def start(self) -> None:
    pass

  async def close(self) -> None:
    pass

  def apply_state(self, state: JsonValue) -> None:
    raise NotImplementedError

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    self._sealed = True
    await self._app(scope, receive, send)

  def unavailable_response(self) -> Response:
    return JSONResponse({"detail": "Microservice is not ready."}, status_code=503)

  async def _live_endpoint(self, request: Request) -> Response:
    return Response(status_code=204)

  async def _ready_endpoint(self, request: Request) -> Response:
    return Response(status_code=204) if self.ready else self.unavailable_response()

  async def _drained_endpoint(self, request: Request) -> Response:
    return Response(status_code=204 if not self._accepting else 503)

  async def _schema_endpoint(self, request: Request) -> Response:
    return JSONResponse(
      self.dynamic_schema(root_path=request.scope.get("root_path", ""))
    )

  async def _state_endpoint(self, request: Request) -> Response:
    if type(self).apply_state is Microservice.apply_state:
      return JSONResponse(
        {"detail": "This microservice does not consume overseer state."},
        status_code=503,
      )
    if request_content_type(request) != "application/json":
      return JSONResponse(
        {"detail": "Overseer state requires application/json."}, status_code=415
      )
    try:
      state: JsonValue = await request.json()
      self.apply_state(state)
    except JSONDecodeError, UnicodeDecodeError:
      return JSONResponse(
        {"detail": "Request body is not valid JSON."}, status_code=400
      )
    except (TypeError, ValueError) as exc:
      return JSONResponse(
        {"detail": "Overseer state was rejected.", "message": str(exc)},
        status_code=409,
      )
    return Response(status_code=204)

  @asynccontextmanager
  async def _lifespan(self, app: Starlette) -> AsyncIterator[None]:
    await self._emit("starting")
    try:
      await self.start()
    except BaseException as exc:
      await self._emit("start_failed", error=str(exc))
      raise
    self._running = True
    await self._emit("started")
    try:
      yield
    finally:
      self._running = False
      await self._emit("stopping")
      try:
        await self.close()
      except BaseException as exc:
        await self._emit("stop_failed", error=str(exc))
        raise
      await self._emit("stopped")

  async def _emit(self, event: str, **attributes: Any) -> None:
    item = LifecycleEvent(self.kind, event, attributes)
    for observer in tuple(self._observers):
      await observer(item)

  async def _emit_operation(
    self, operation: str, phase: str, attributes: dict[str, Any]
  ) -> None:
    item = OperationEvent(self.kind, operation, phase, attributes)
    for observer in tuple(self._operation_observers):
      await observer(item)

  def _implementation_hash(self) -> str:
    encoded = json.dumps(
      self.schema_document(""),
      ensure_ascii=False,
      separators=(",", ":"),
      sort_keys=True,
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

  @staticmethod
  def _root_path(value: str) -> str:
    if not value or value == "/":
      return ""
    if not value.startswith("/") or value.startswith("//"):
      raise ValueError("root_path must be an absolute URL path.")
    return value.rstrip("/")
