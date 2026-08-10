import asyncio
from base64 import b64decode, urlsafe_b64encode
from binascii import Error
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from re import fullmatch
from typing import Protocol

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from micro._microservices import Microservice

from ._source import QueueBackendDelivery, QueueObservation

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

  async def request(self, channel: str, payload: bytes, *, timeout: float) -> bytes: ...

  async def consume(
    self, channel: str, consumer: str, *, timeout: float
  ) -> QueueBackendDelivery | None: ...

  async def acknowledge(self, receipt: str) -> None: ...

  async def retry(self, receipt: str, *, delay: float = 0) -> None: ...

  async def dead_letter(self, receipt: str) -> None: ...

  async def respond(self, receipt: str, reply: str, payload: bytes) -> None: ...

  async def observe(self) -> QueueObservation: ...

  async def close(self) -> None: ...


class Queue(Microservice):
  """ASGI owner of a distributed queue backend's complete data plane."""

  def __init__(
    self,
    *,
    backend: QueueBackend,
    consume_timeout: float = 1.0,
    max_payload_size: int = 8 * 1024 * 1024,
    max_response_size: int = 8 * 1024 * 1024,
  ) -> None:
    if not 0 < consume_timeout <= 30:
      raise ValueError("consume_timeout must be between 0 and 30 seconds.")
    super().__init__("queue")
    self.backend = backend
    self.consume_timeout = consume_timeout
    if max_payload_size <= 0 or max_response_size <= 0:
      raise ValueError("Queue size limits must be positive.")
    self.max_payload_size = max_payload_size
    self.max_response_size = max_response_size
    self._active = 0
    self._idle = asyncio.Event()
    self._idle.set()
    self.add_route(
      "/channels/{channel}",
      self._publish,
      methods=("POST",),
      name="queue:publish",
    )
    self.add_route(
      "/channels/{channel}/request",
      self._request,
      methods=("POST",),
      name="queue:request",
    )
    self.add_route(
      "/channels/{channel}/consumers/{consumer}",
      self._consume,
      methods=("POST",),
      name="queue:consume",
    )
    for action in ("acknowledge", "retry", "respond", "dead_letter"):
      self.add_route(
        f"/deliveries/{action}",
        getattr(self, f"_{action}"),
        methods=("POST",),
        name=f"queue:{action}",
      )
    self.add_route(
      "/queue/observations",
      self._observations,
      methods=("GET",),
      name="queue:observations",
    )

  async def start(self) -> None:
    await self.backend.start()

  async def close(self) -> None:
    self.drain()
    await self._idle.wait()
    await self.backend.close()

  async def _publish(self, request: Request) -> Response:
    if not self.accepting:
      return JSONResponse({"detail": "Queue is draining."}, status_code=503)
    try:
      channel = validate_channel(request.path_params["channel"])
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    async with self._operation("publish"):
      payload = await _bounded_body(request, self.max_payload_size)
      if payload is None:
        return JSONResponse({"detail": "Queue payload is too large."}, status_code=413)
      await self.backend.publish(channel, payload)
    return Response(status_code=204)

  async def _request(self, request: Request) -> Response:
    if not self.accepting:
      return JSONResponse({"detail": "Queue is draining."}, status_code=503)
    try:
      channel = validate_channel(request.path_params["channel"])
      timeout = float(request.query_params.get("timeout", "30"))
      if not 0 < timeout <= 300:
        raise ValueError("Request timeout must be between 0 and 300 seconds.")
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    try:
      request_payload = await _bounded_body(request, self.max_payload_size)
      if request_payload is None:
        return JSONResponse({"detail": "Queue payload is too large."}, status_code=413)
      async with self._operation("request"):
        payload = await self.backend.request(channel, request_payload, timeout=timeout)
    except TimeoutError:
      return JSONResponse({"detail": "Queue request timed out."}, status_code=504)
    if len(payload) > self.max_response_size:
      return JSONResponse({"detail": "Queue response is too large."}, status_code=502)
    return Response(payload, media_type="application/octet-stream")

  async def _consume(self, request: Request) -> Response:
    if not self.accepting:
      return JSONResponse({"detail": "Queue is draining."}, status_code=503)
    try:
      channel = validate_channel(request.path_params["channel"])
      consumer = validate_channel(request.path_params["consumer"])
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    async with self._operation("consume"):
      delivery = await self.backend.consume(
        channel, consumer, timeout=self.consume_timeout
      )
    if delivery is None:
      return Response(status_code=204)
    headers = {"micro-receipt": _encode_capability(delivery.receipt)}
    if delivery.reply is not None:
      headers["micro-reply"] = _encode_capability(delivery.reply)
    return Response(
      delivery.payload,
      media_type="application/octet-stream",
      headers=headers,
    )

  async def _acknowledge(self, request: Request) -> Response:
    try:
      receipt = _capability(request, "micro-receipt")
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    async with self._operation("acknowledge"):
      await self.backend.acknowledge(receipt)
    return Response(status_code=204)

  async def _retry(self, request: Request) -> Response:
    try:
      receipt = _capability(request, "micro-receipt")
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    try:
      delay = float(request.query_params.get("delay", "0"))
      if not 0 <= delay <= 86400:
        raise ValueError
    except ValueError:
      return JSONResponse(
        {"detail": "Retry delay must be 0 through 86400."}, status_code=422
      )
    async with self._operation("retry"):
      await self.backend.retry(receipt, delay=delay)
    return Response(status_code=204)

  async def _respond(self, request: Request) -> Response:
    try:
      receipt = _capability(request, "micro-receipt")
      reply = _capability(request, "micro-reply")
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    payload = await _bounded_body(request, self.max_response_size)
    if payload is None:
      return JSONResponse({"detail": "Queue response is too large."}, status_code=413)
    async with self._operation("respond"):
      await self.backend.respond(receipt, reply, payload)
    return Response(status_code=204)

  async def _dead_letter(self, request: Request) -> Response:
    try:
      receipt = _capability(request, "micro-receipt")
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=422)
    async with self._operation("dead_letter"):
      await self.backend.dead_letter(receipt)
    return Response(status_code=204)

  async def _observations(self, request: Request) -> Response:
    observation = await self.backend.observe()
    return JSONResponse(
      {
        "connected": observation.connected,
        "pending": observation.pending,
        "consumers": observation.consumers,
        "active_operations": self._active,
        "accepting": self.accepting,
      }
    )

  @asynccontextmanager
  async def _operation(self, name: str) -> AsyncIterator[None]:
    self._active += 1
    self._idle.clear()
    try:
      async with self.operation(name):
        yield
    finally:
      self._active -= 1
      if self._active == 0:
        self._idle.set()


def _encode_capability(value: str) -> str:
  return urlsafe_b64encode(value.encode()).decode().rstrip("=")


def _capability(request: Request, name: str) -> str:
  encoded = request.headers.get(name)
  if encoded is None:
    raise ValueError(f"Delivery requires the {name} header.")
  try:
    value = b64decode(
      f"{encoded}{'=' * (-len(encoded) % 4)}",
      altchars=b"-_",
      validate=True,
    ).decode()
  except (Error, UnicodeDecodeError, ValueError) as exc:
    raise ValueError(f"Delivery has an invalid {name} header.") from exc
  if not value:
    raise ValueError(f"Delivery has an empty {name} header.")
  return value


async def _bounded_body(request: Request, limit: int) -> bytes | None:
  body = bytearray()
  async for chunk in request.stream():
    if len(body) + len(chunk) > limit:
      return None
    body.extend(chunk)
  return bytes(body)
