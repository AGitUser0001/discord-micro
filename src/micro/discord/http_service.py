import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from time import monotonic
from typing import Any, Literal, Protocol
from urllib.parse import quote, urlencode

import httpx2
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic_core import from_json, to_json

from micro._microservices import Microservice
from micro.queue import QueueClient

from .http_operations import (
  HTTP_OPERATIONS,
  DiscordHTTPOperation,
  DiscordOperationId,
  GeneratedDiscordHTTPClient,
)

DISCORD_HTTP_CHANNEL = "discord.http"


class DiscordHTTPRequest(BaseModel):
  """One generated Discord OpenAPI operation invocation."""

  model_config = ConfigDict(extra="forbid", frozen=True)
  operation: DiscordOperationId
  data: dict[str, JsonValue]
  idempotency_key: str | None = None


class DiscordHTTPResponse(BaseModel):
  """Unmodified Discord response status, headers, and body."""

  model_config = ConfigDict(
    extra="forbid", frozen=True, ser_json_bytes="base64", val_json_bytes="base64"
  )
  status: int = Field(ge=100, le=599)
  headers: tuple[tuple[str, str], ...]
  body: bytes


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
  """Queue worker that validates and executes generated Discord operations."""

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
    operation = HTTP_OPERATIONS[request.operation]
    unknown_fields = request.data.keys() - operation.input_model.model_fields.keys()
    if unknown_fields:
      raise ValueError(
        f"Operation {operation.id!r} received unknown fields: "
        f"{', '.join(sorted(unknown_fields))}."
      )
    data = operation.input_model.model_validate_json(to_json(request.data))
    route = _route_key(operation, data)
    for attempt in range(self._max_attempts):
      await self._coordinator.acquire(route)
      response = await self._execute_operation(operation, data)
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

  async def _execute_operation(
    self, operation: DiscordHTTPOperation, request: BaseModel
  ) -> httpx2.Response:
    values = request.model_dump(mode="json", by_alias=True, exclude_none=True)
    path = operation.path
    for field in operation.path_fields:
      path = path.replace("{" + field + "}", quote(str(values[field]), safe=""))
    query = {
      field: values[field] for field in operation.query_fields if field in values
    }
    headers = {
      field: str(values[field]) for field in operation.header_fields if field in values
    }
    body = getattr(request, "body", None)
    content_type = values.get("content_type")
    if body is None:
      return await self._http.request(
        operation.method, path, params=query, headers=headers
      )
    if content_type == "application/json":
      headers["content-type"] = content_type
      return await self._http.request(
        operation.method,
        path,
        params=query,
        headers=headers,
        content=to_json(_body_mapping(body, mode="json")),
      )
    if content_type == "application/x-www-form-urlencoded":
      headers["content-type"] = content_type
      return await self._http.request(
        operation.method,
        path,
        params=query,
        headers=headers,
        content=urlencode(_body_mapping(body, mode="json"), doseq=True),
      )
    if content_type == "multipart/form-data":
      form, files = _multipart(_body_mapping(body, mode="python"))
      return await self._http.request(
        operation.method,
        path,
        params=query,
        headers=headers,
        data=form,
        files=files,
      )
    raise ValueError(
      f"Operation {operation.id!r} has unsupported content type {content_type!r}."
    )

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


class DiscordHTTPClient(GeneratedDiscordHTTPClient[DiscordHTTPResponse]):
  """Generated Discord API methods transported through Micro Queue."""

  def __init__(self, queue: QueueClient | None = None) -> None:
    self.queue = queue or QueueClient()

  def apply_state(self, state: JsonValue) -> None:
    self.queue.apply_state(state)

  async def request(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    payload = await self.queue.request(
      DISCORD_HTTP_CHANNEL, request.model_dump_json().encode()
    )
    return DiscordHTTPResponse.model_validate_json(payload)

  async def _request_operation(
    self, operation: DiscordOperationId, request: BaseModel
  ) -> DiscordHTTPResponse:
    return await self.request(
      DiscordHTTPRequest(
        operation=operation,
        data=request.model_dump(mode="json", by_alias=True),
      )
    )

  async def aclose(self) -> None:
    await self.queue.aclose()


def _route_key(operation: DiscordHTTPOperation, request: BaseModel) -> str:
  values = request.model_dump(mode="json", by_alias=True)
  major = tuple(
    str(values[field])
    for field in ("channel_id", "guild_id", "webhook_id", "webhook_token")
    if field in values and values[field] is not None
  )
  return ":".join((operation.id, *major))


def _multipart(body: Any) -> tuple[dict[str, Any], dict[str, Any]]:
  if not isinstance(body, dict):
    raise TypeError("Multipart Discord request bodies must be objects.")
  form: dict[str, Any] = {}
  files: dict[str, Any] = {}
  for name, value in body.items():
    if isinstance(value, bytes):
      files[name] = (name, value)
    else:
      form[name] = value
  return form, files


def _body_mapping(body: Any, *, mode: Literal["json", "python"]) -> dict[str, Any]:
  if isinstance(body, BaseModel):
    return body.model_dump(mode=mode, by_alias=True, exclude_none=True)
  if isinstance(body, dict):
    return body
  raise TypeError("Discord request bodies must be objects.")


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
  "MemoryRateLimits",
  "RateLimitCoordinator",
)
