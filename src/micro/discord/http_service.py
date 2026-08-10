import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from time import monotonic
from typing import Protocol

import httpx2
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic_core import from_json

from micro._microservices import Microservice
from micro.queue import QueueClient

from .models.http import ApplicationCommandCreateRequest, MessageCreateRequest

DISCORD_HTTP_CHANNEL = "discord.http"


class DiscordHTTPRequest(BaseModel):
  """Discord REST work item carried through Micro Queue."""

  model_config = ConfigDict(
    extra="forbid", frozen=True, ser_json_bytes="base64", val_json_bytes="base64"
  )
  method: str = Field(pattern=r"^(DELETE|GET|PATCH|POST|PUT)$")
  path: str = Field(pattern=r"^/")
  headers: tuple[tuple[str, str], ...] = ()
  body: bytes = b""
  idempotency_key: str | None = None


class DiscordHTTPResponse(BaseModel):
  """Unmodified Discord response data suitable for typed or raw callers."""

  model_config = ConfigDict(
    extra="forbid", frozen=True, ser_json_bytes="base64", val_json_bytes="base64"
  )
  status: int = Field(ge=100, le=599)
  headers: tuple[tuple[str, str], ...]
  body: bytes


class DiscordMultipartPart(BaseModel):
  model_config = ConfigDict(
    extra="forbid", frozen=True, ser_json_bytes="base64", val_json_bytes="base64"
  )
  name: str
  data: bytes
  filename: str | None = None
  content_type: str = "application/octet-stream"


class RateLimitCoordinator(Protocol):
  async def acquire(self, route: str) -> None: ...
  async def observe(self, route: str, response: DiscordHTTPResponse) -> None: ...
  async def completed(self, key: str) -> DiscordHTTPResponse | None: ...
  async def complete(self, key: str, response: DiscordHTTPResponse) -> None: ...


@dataclass(slots=True)
class _Bucket:
  remaining: int = 1
  reset_at: float = 0.0


class MemoryRateLimits:
  """Rate-limit state shareable by multiple worker objects in one host."""

  def __init__(self) -> None:
    self._buckets: dict[str, _Bucket] = {}
    self._global_reset = 0.0
    self._lock = asyncio.Lock()
    self._completed: dict[str, DiscordHTTPResponse] = {}

  async def acquire(self, route: str) -> None:
    while True:
      async with self._lock:
        now = monotonic()
        bucket = self._buckets.setdefault(route, _Bucket())
        delay = max(self._global_reset, bucket.reset_at) - now
        if delay <= 0:
          if bucket.remaining > 0:
            bucket.remaining -= 1
          return
      await asyncio.sleep(delay)

  async def observe(self, route: str, response: DiscordHTTPResponse) -> None:
    headers = {name.lower(): value for name, value in response.headers}
    async with self._lock:
      bucket_name = headers.get("x-ratelimit-bucket", route)
      bucket = self._buckets.setdefault(bucket_name, _Bucket())
      self._buckets[route] = bucket
      if (remaining := headers.get("x-ratelimit-remaining")) is not None:
        bucket.remaining = max(0, int(float(remaining)))
      delay = _retry_after(response, headers)
      if delay > 0:
        reset = monotonic() + delay
        if headers.get("x-ratelimit-global") == "true":
          self._global_reset = max(self._global_reset, reset)
        else:
          bucket.reset_at = max(bucket.reset_at, reset)

  async def completed(self, key: str) -> DiscordHTTPResponse | None:
    async with self._lock:
      return self._completed.get(key)

  async def complete(self, key: str, response: DiscordHTTPResponse) -> None:
    async with self._lock:
      if len(self._completed) >= 10_000:
        self._completed.pop(next(iter(self._completed)))
      self._completed[key] = response


class DiscordHTTPWorker(Microservice):
  """Normal Micro worker that performs queued Discord REST requests."""

  def __init__(
    self,
    token: str,
    *,
    api_url: str = "https://discord.com/api/v10",
    transport: httpx2.AsyncBaseTransport | None = None,
    coordinator: RateLimitCoordinator | None = None,
    max_attempts: int = 4,
  ) -> None:
    if not token:
      raise ValueError("token cannot be empty.")
    if not 1 <= max_attempts <= 10:
      raise ValueError("max_attempts must be between 1 and 10.")
    self.queue = QueueClient(transport=transport)
    self._http = httpx2.AsyncClient(
      base_url=api_url,
      transport=transport,
      headers={"authorization": f"Bot {token}", "user-agent": "DiscordBot (Micro)"},
    )
    self._coordinator = coordinator or MemoryRateLimits()
    self._max_attempts = max_attempts
    self._consumer: asyncio.Task[None] | None = None
    self._topology_ready = asyncio.Event()
    super().__init__("discord.http")

  def apply_state(self, state: JsonValue) -> None:
    self.queue.apply_state(state)
    self._topology_ready.set()

  async def start(self) -> None:
    self._consumer = asyncio.create_task(self._consume(), name="micro.discord.http")

  async def close(self) -> None:
    if self._consumer is not None:
      self._consumer.cancel()
      await asyncio.gather(self._consumer, return_exceptions=True)
      self._consumer = None
    await self._http.aclose()
    await self.queue.aclose()

  async def execute(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    if request.idempotency_key is not None:
      completed = await self._coordinator.completed(request.idempotency_key)
      if completed is not None:
        return completed
    route = _route_key(request.method, request.path)
    for attempt in range(self._max_attempts):
      await self._coordinator.acquire(route)
      response = await self._http.request(
        request.method,
        request.path,
        headers=dict(request.headers),
        content=request.body,
      )
      result = DiscordHTTPResponse(
        status=response.status_code,
        headers=tuple(response.headers.multi_items()),
        body=response.content,
      )
      await self._coordinator.observe(route, result)
      if response.status_code != 429 or attempt + 1 == self._max_attempts:
        if request.idempotency_key is not None:
          await self._coordinator.complete(request.idempotency_key, result)
        return result
    raise AssertionError("Discord HTTP retry loop did not return.")

  async def _consume(self) -> None:
    await self._topology_ready.wait()
    while True:
      delivery = await self.queue.consume(DISCORD_HTTP_CHANNEL, "micro-discord-http")
      try:
        request = DiscordHTTPRequest.model_validate_json(delivery.payload)
        response = await self.execute(request)
        await delivery.respond(response.model_dump_json().encode())
      except ValueError:
        await delivery.acknowledge()
      except Exception:
        await delivery.retry()


class DiscordHTTPClient:
  """Typed conveniences over the raw Discord HTTP queue contract."""

  def __init__(self, queue: QueueClient | None = None) -> None:
    self.queue = queue or QueueClient()

  def apply_state(self, state: JsonValue) -> None:
    self.queue.apply_state(state)

  async def request(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    payload = await self.queue.request(
      DISCORD_HTTP_CHANNEL, request.model_dump_json().encode()
    )
    return DiscordHTTPResponse.model_validate_json(payload)

  async def create_message(
    self, channel_id: int | str, request: MessageCreateRequest
  ) -> DiscordHTTPResponse:
    return await self._json("POST", f"/channels/{channel_id}/messages", request)

  async def create_global_command(
    self, application_id: int | str, request: ApplicationCommandCreateRequest
  ) -> DiscordHTTPResponse:
    return await self._json("POST", f"/applications/{application_id}/commands", request)

  async def get_guild(self, guild_id: int | str) -> DiscordHTTPResponse:
    """Fetch a guild while preserving Discord's exact response representation."""
    return await self.request(
      DiscordHTTPRequest(method="GET", path=f"/guilds/{guild_id}")
    )

  async def interaction_callback(
    self, interaction_id: int | str, token: str, request: BaseModel
  ) -> DiscordHTTPResponse:
    return await self._json(
      "POST", f"/interactions/{interaction_id}/{token}/callback", request
    )

  async def multipart(
    self,
    method: str,
    path: str,
    parts: tuple[DiscordMultipartPart, ...],
    *,
    max_size: int = 8 * 1024 * 1024,
  ) -> DiscordHTTPResponse:
    boundary = "micro-discord-boundary"
    body = bytearray()
    for part in parts:
      disposition = f'form-data; name="{part.name}"'
      if part.filename is not None:
        disposition += f'; filename="{part.filename}"'
      chunk = (
        (
          f"--{boundary}\r\nContent-Disposition: {disposition}\r\n"
          f"Content-Type: {part.content_type}\r\n\r\n"
        ).encode()
        + part.data
        + b"\r\n"
      )
      if len(body) + len(chunk) + len(boundary) + 6 > max_size:
        raise ValueError("Multipart request exceeds its configured size limit.")
      body.extend(chunk)
    body.extend(f"--{boundary}--\r\n".encode())
    return await self.request(
      DiscordHTTPRequest(
        method=method,
        path=path,
        headers=(("content-type", f"multipart/form-data; boundary={boundary}"),),
        body=bytes(body),
      )
    )

  async def _json(
    self, method: str, path: str, request: BaseModel
  ) -> DiscordHTTPResponse:
    return await self.request(
      DiscordHTTPRequest(
        method=method,
        path=path,
        headers=(("content-type", "application/json"),),
        body=request.model_dump_json(exclude_none=True).encode(),
      )
    )

  async def aclose(self) -> None:
    await self.queue.aclose()


def _route_key(method: str, path: str) -> str:
  return f"{method}:" + "/".join(
    part if not part.isdecimal() else ":id" for part in path.strip("/").split("/")
  )


def _retry_after(response: DiscordHTTPResponse, headers: Mapping[str, str]) -> float:
  if (value := headers.get("retry-after")) is not None:
    return max(0.0, float(value))
  if response.status != 429:
    return 0.0
  try:
    body = from_json(response.body)
  except ValueError:
    return 0.0
  if isinstance(body, dict) and isinstance(body.get("retry_after"), int | float):
    return max(0.0, float(body["retry_after"]))
  return 0.0


__all__ = (
  "DISCORD_HTTP_CHANNEL",
  "DiscordHTTPClient",
  "DiscordHTTPRequest",
  "DiscordHTTPResponse",
  "DiscordHTTPWorker",
  "DiscordMultipartPart",
  "MemoryRateLimits",
  "RateLimitCoordinator",
)
