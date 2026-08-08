import hashlib
import json
from collections.abc import Awaitable, Callable
from json import JSONDecodeError
from typing import Protocol

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


class StateReceiver(Protocol):
  def apply_state(self, state: JsonValue) -> None: ...


class DuplicateEndpointError(ValueError):
  pass


class Microservice:
  """Shared ASGI and lifecycle machinery for every networked Micro worker."""

  def __init__(
    self,
    kind: str,
    *,
    state_receiver: StateReceiver | None = None,
  ) -> None:
    if not kind:
      raise ValueError("Microservice kind cannot be empty.")
    self.kind = kind
    self._state_receiver = state_receiver
    self._accepting = True
    self._running = False
    self._sealed = False
    self._paths: set[str] = set(_STANDARD_PATHS)
    self._app = Starlette(
      routes=[
        Route("/health/live", self._live_endpoint, methods=["GET"]),
        Route("/health/ready", self._ready_endpoint, methods=["GET"]),
        Route("/health/drained", self._drained_endpoint, methods=["GET"]),
        Route("/schema", self._schema_endpoint, methods=["GET"]),
        Route("/state", self._state_endpoint, methods=["POST"]),
      ]
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

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    self._sealed = True
    if scope["type"] != "lifespan":
      await self._app(scope, receive, send)
      return
    await self._lifespan(receive, send)

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
    if self._state_receiver is None:
      return JSONResponse(
        {"detail": "This microservice does not consume overseer state."},
        status_code=503,
      )
    content_type = request.headers.get("content-type", "").partition(";")[0].strip()
    if content_type != "application/json":
      return JSONResponse(
        {"detail": "Overseer state requires application/json."}, status_code=415
      )
    try:
      state: JsonValue = await request.json()
      self._state_receiver.apply_state(state)
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

  async def _lifespan(self, receive: Receive, send: Send) -> None:
    while True:
      message = await receive()
      if message["type"] == "lifespan.startup":
        try:
          await self.start()
        except BaseException as exc:
          await send({"type": "lifespan.startup.failed", "message": str(exc)})
          return
        self._running = True
        await send({"type": "lifespan.startup.complete"})
      elif message["type"] == "lifespan.shutdown":
        self._running = False
        try:
          await self.close()
        except BaseException as exc:
          await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
          return
        await send({"type": "lifespan.shutdown.complete"})
        return

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
