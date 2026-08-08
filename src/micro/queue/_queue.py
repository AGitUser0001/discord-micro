from re import fullmatch
from typing import Protocol

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from micro._microservices import Microservice

_CHANNEL_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


def validate_channel(channel: str) -> str:
  if fullmatch(_CHANNEL_PATTERN, channel) is None:
    raise ValueError(
      "Queue channels may contain letters, numbers, dots, underscores, and "
      "hyphens, and must start and end with a letter or number."
    )
  return channel


class QueueBackend(Protocol):
  async def start(self) -> None: ...

  async def publish(self, channel: str, payload: bytes) -> None: ...

  async def close(self) -> None: ...


class Queue(Microservice):
  """Minimal ASGI ingress for a distributed queue backend."""

  def __init__(self, *, backend: QueueBackend) -> None:
    super().__init__("queue")
    self.backend = backend
    self.add_route(
      "/channels/{channel}",
      self._publish,
      methods=("POST",),
      name="queue:publish",
    )

  async def start(self) -> None:
    await self.backend.start()

  async def close(self) -> None:
    await self.backend.close()

  async def _publish(self, request: Request) -> Response:
    if not self.accepting:
      return JSONResponse({"detail": "Queue is draining."}, status_code=503)
    try:
      channel = validate_channel(request.path_params["channel"])
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    await self.backend.publish(channel, await request.body())
    return Response(status_code=204)
