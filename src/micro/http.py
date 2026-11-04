"""A template component bridging HTTP to a Micro deployment.

Use it as-is (`micro run micro.http:HTTPBridge`) for health probes, discovery,
and an admin API, or subclass it and add routes to `app` before it starts.
It serves only what it exposes; put it behind your own authentication.
"""

import asyncio
import json
import os
from contextlib import suppress
from typing import Any

from nats.errors import NoRespondersError
from nats.errors import TimeoutError as NatsTimeoutError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from micro import subjects
from micro.runtime import Component

_ERROR_STATUS = {
  "invalid_input": 422,
  "incompatible_schema": 422,
  "handler_failed": 500,
  "invalid_output": 500,
}
"""Framework error codes; application `ServiceError` codes map to 400."""


class HTTPBridge(Component):
  """Serves an ASGI app inside a runtime.

  Built-in routes:

  * `GET /health/live`, `GET /health/ready` for this process.
  * `GET /components` lists every live component in the deployment.
  * `POST /requests/{request_id}` forwards a JSON body to a service request.
  * `POST /events/{event_id}` publishes a JSON body as an event.
  * `GET /gateway`, `PUT /gateway/shards`, `POST /gateway/roll`,
    `PUT /gateway/presence` operate the Discord Gateway.
  """

  kind = "http"

  def __init__(
    self,
    *,
    host: str | None = None,
    port: int | None = None,
    name: str = "http",
    request_timeout: float = 30.0,
  ) -> None:
    super().__init__(name)
    self.host = host or os.environ.get("MICRO_HTTP_HOST", "127.0.0.1")
    self.port = (
      port if port is not None else int(os.environ.get("MICRO_HTTP_PORT", "8080"))
    )
    self.request_timeout = request_timeout
    self.app = Starlette(routes=self.routes())
    self._server: Any = None

  def routes(self) -> list[Route]:
    """Override to change the built-in routes; add more to `app` directly."""
    return [
      Route("/health/live", self.live, methods=["GET"]),
      Route("/health/ready", self.ready_probe, methods=["GET"]),
      Route("/components", self.components, methods=["GET"]),
      Route("/requests/{request_id}", self.request, methods=["POST"]),
      Route("/events/{event_id}", self.event, methods=["POST"]),
      Route("/gateway", self.gateway_status, methods=["GET"]),
      Route("/gateway/shards", self.gateway_shards, methods=["PUT"]),
      Route("/gateway/roll", self.gateway_roll, methods=["POST"]),
      Route("/gateway/presence", self.gateway_presence, methods=["PUT"]),
    ]

  async def on_start(self) -> None:
    import uvicorn

    config = uvicorn.Config(
      self.app, host=self.host, port=self.port, log_level="warning", lifespan="off"
    )
    self._server = uvicorn.Server(config)
    self._server.install_signal_handlers = lambda: None
    self.spawn(self._server.serve(), name="server")
    while not self._server.started:
      await asyncio.sleep(0.01)
    await self.runtime.register(
      self, metadata={"url": f"http://{self.host}:{self.port}"}
    )

  async def on_close(self) -> None:
    if self._server is not None:
      self._server.should_exit = True
      with suppress(Exception):
        await self._server.shutdown()

  # Routes ----------------------------------------------------------------------

  async def live(self, request: Request) -> Response:
    return Response(status_code=204)

  async def ready_probe(self, request: Request) -> Response:
    return Response(status_code=204 if self.runtime.ready else 503)

  async def components(self, request: Request) -> Response:
    return JSONResponse(
      [entry.model_dump() for entry in self.runtime.directory.entries()]
    )

  async def request(self, request: Request) -> Response:
    request_id = request.path_params["request_id"]
    try:
      subject = subjects.request(request_id)
    except ValueError:
      return JSONResponse({"code": "invalid_input", "message": "Bad request ID."}, 400)
    try:
      reply = await self.runtime.nats.request(
        subject, await request.body(), timeout=self.request_timeout
      )
    except NoRespondersError:
      return JSONResponse(
        {"code": "unavailable", "message": "No service handles it."}, 503
      )
    except NatsTimeoutError:
      return JSONResponse({"code": "timeout", "message": "The request timed out."}, 504)
    if (reply.headers or {}).get("Micro-Status") == "error":
      body = json.loads(reply.data)
      return JSONResponse(body, _ERROR_STATUS.get(body.get("code"), 400))
    return Response(reply.data, media_type="application/json")

  async def event(self, request: Request) -> Response:
    try:
      subject = subjects.event(request.path_params["event_id"])
    except ValueError:
      return JSONResponse({"code": "invalid_input", "message": "Bad event ID."}, 400)
    await self.runtime.jetstream.publish(
      subject, await request.body(), stream=subjects.EVENTS_STREAM
    )
    return Response(status_code=202)

  async def gateway_status(self, request: Request) -> Response:
    status = await self._gateway().status()
    return JSONResponse(
      {
        "desired": status.desired.model_dump() if status.desired else None,
        "active": status.active.model_dump() if status.active else None,
        "workers": [worker.id for worker in status.workers],
        "leases": {key: lease.model_dump() for key, lease in status.leases.items()},
      }
    )

  async def gateway_shards(self, request: Request) -> Response:
    body = await request.json()
    generation = await self._gateway().set_shard_count(int(body["count"]))
    return JSONResponse(generation.model_dump(), 202)

  async def gateway_roll(self, request: Request) -> Response:
    return JSONResponse((await self._gateway().roll()).model_dump(), 202)

  async def gateway_presence(self, request: Request) -> Response:
    from micro.gateway import ActivityUpdate

    body = await request.json()
    activity = body.get("activity")
    await self._gateway().update_presence(
      status=body.get("status", "online"),
      activity=ActivityUpdate.model_validate(activity) if activity else None,
      afk=bool(body.get("afk", False)),
    )
    return Response(status_code=204)

  def _gateway(self) -> Any:
    from micro.gateway import GatewayControl

    return GatewayControl(self.runtime)
