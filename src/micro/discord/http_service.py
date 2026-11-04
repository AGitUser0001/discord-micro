import asyncio
import hashlib
import json
import logging
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from time import monotonic, time
from typing import Any, Literal
from urllib.parse import quote, urlencode

import httpx2
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import NoRespondersError
from nats.errors import TimeoutError as NatsTimeoutError
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic_core import from_json, to_json

from micro import subjects
from micro.errors import RemoteError, RequestTimeoutError, RoutingError
from micro.runtime import Component, Presence, Registration, Runtime

from .http_operations import (
  HTTP_OPERATIONS,
  DiscordHTTPOperation,
  DiscordOperationId,
  GeneratedDiscordHTTPClient,
)

logger = logging.getLogger("micro")

WORKER_KIND = "discord.http"
_STATUS_HEADER = "Micro-Status"


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


class _GlobalLimit(BaseModel):
  until: float


@dataclass(slots=True)
class _Bucket:
  remaining: int = 1
  reset_at: float = 0.0


class RateLimits:
  """In-memory Discord rate-limit buckets for one HTTP worker.

  Requests are partitioned so every request sharing a bucket reaches the same
  worker, so this state never needs to be shared. Only the global limit is
  announced to the other workers.
  """

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

  async def observe(self, route: str, response: DiscordHTTPResponse) -> float | None:
    """Record a response; returns the wall-clock end of a global limit, if any."""
    headers = {name.lower(): value for name, value in response.headers}
    async with self._lock:
      bucket_name = headers.get("x-ratelimit-bucket", route)
      major = route.partition(":")[2]
      bucket = self._buckets.setdefault(f"{bucket_name}:{major}", _Bucket())
      self._buckets[route] = bucket
      if (remaining := headers.get("x-ratelimit-remaining")) is not None:
        bucket.remaining = max(0, int(float(remaining)))
      if (reset_after := headers.get("x-ratelimit-reset-after")) is not None and (
        bucket.remaining == 0
      ):
        bucket.reset_at = max(bucket.reset_at, monotonic() + float(reset_after))
      delay = _retry_after(response, headers)
      if delay <= 0:
        return None
      if _is_global_rate_limit(response, headers):
        self._global_reset = max(self._global_reset, monotonic() + delay)
        return time() + delay
      bucket.reset_at = max(bucket.reset_at, monotonic() + delay)
      return None

  def block_globally_until(self, wall_clock: float) -> None:
    self._global_reset = max(self._global_reset, monotonic() + wall_clock - time())

  def completed(self, key: str) -> DiscordHTTPResponse | None:
    return self._completed.get(key)

  def complete(self, key: str, response: DiscordHTTPResponse) -> None:
    if len(self._completed) >= 10_000:
      self._completed.pop(next(iter(self._completed)))
    self._completed[key] = response


class DiscordHTTPWorker(Component):
  """Executes generated Discord operations for one partition of rate-limit buckets.

  Run any number of workers; callers route each request by rendezvous hashing
  over the live workers, so a bucket's requests share one worker and partitions
  move minimally when workers join or leave. The token comes from the host
  (`DISCORD_TOKEN` by default) and is never stored in NATS.
  """

  kind = WORKER_KIND

  def __init__(
    self,
    token: str | None = None,
    *,
    name: str = "discord.http",
    api_url: str = "https://discord.com/api/v10",
    transport: httpx2.AsyncBaseTransport | None = None,
    max_attempts: int = 4,
    concurrency: int = 256,
  ) -> None:
    token = token if token is not None else os.environ.get("DISCORD_TOKEN")
    if not token:
      raise ValueError("A Discord token is required (argument or DISCORD_TOKEN).")
    if not 1 <= max_attempts <= 10:
      raise ValueError("max_attempts must be between 1 and 10.")
    super().__init__(name)
    self._token = token
    self._api_url = api_url
    self._transport = transport
    self._max_attempts = max_attempts
    self._slots = asyncio.Semaphore(concurrency)
    self.rate_limits = RateLimits()
    self._http: httpx2.AsyncClient | None = None
    self._subscriptions: list[Subscription] = []
    self._presence: Presence | None = None
    self.address = subjects.token(os.urandom(8).hex())

  async def on_start(self) -> None:
    self._http = httpx2.AsyncClient(
      base_url=self._api_url,
      transport=self._transport,
      headers={"user-agent": "DiscordBot (Micro)", "authorization": f"Bot {self._token}"},
    )
    nats = self.runtime.nats
    self._subscriptions = [
      await nats.subscribe(subjects.http_worker(self.address), cb=self._on_request),
      await nats.subscribe(subjects.HTTP_GLOBAL_LIMIT, cb=self._on_global_limit),
    ]
    self._presence = await self.runtime.register(self, id=self.address)

  async def on_drain(self) -> None:
    # Leave the partition first so callers re-route, then finish what arrived.
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    await self._unsubscribe()

  async def on_close(self) -> None:
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    await self._unsubscribe()
    if self._http is not None:
      await self._http.aclose()
      self._http = None

  async def _unsubscribe(self) -> None:
    subscriptions, self._subscriptions = self._subscriptions, []
    for subscription in subscriptions:
      try:
        await subscription.drain()
      except Exception:
        logger.debug("HTTP worker subscription drain failed", exc_info=True)

  async def _on_global_limit(self, message: Msg) -> None:
    try:
      self.rate_limits.block_globally_until(_GlobalLimit.model_validate_json(message.data).until)
    except ValueError:
      logger.warning("Ignoring an invalid global rate-limit announcement")

  async def _on_request(self, message: Msg) -> None:
    await self._slots.acquire()
    task = asyncio.create_task(self._answer(message))
    task.add_done_callback(lambda _: self._slots.release())

  async def _answer(self, message: Msg) -> None:
    async with self.tracked():
      try:
        request = DiscordHTTPRequest.model_validate_json(message.data)
        body = (await self.execute(request)).model_dump_json().encode()
        headers = {_STATUS_HEADER: "ok"}
      except Exception as exc:
        logger.exception("Discord HTTP request failed")
        code = "invalid_input" if isinstance(exc, ValueError) else "handler_failed"
        body = json.dumps({"code": code, "message": f"{type(exc).__name__}: {exc}"}).encode()
        headers = {_STATUS_HEADER: "error"}
      if message.reply:
        await self.runtime.nats.publish(message.reply, body, headers=headers)

  async def execute(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    if request.idempotency_key is not None:
      completed = self.rate_limits.completed(request.idempotency_key)
      if completed is not None:
        return completed
    operation = HTTP_OPERATIONS[request.operation]
    unknown_fields = request.data.keys() - operation.request_model.model_fields.keys()
    if unknown_fields:
      raise ValueError(
        f"Operation {operation.id!r} received unknown fields: "
        f"{', '.join(sorted(unknown_fields))}."
      )
    data = operation.request_model.model_validate_json(to_json(request.data))
    route = route_key(operation, data)
    for attempt in range(self._max_attempts):
      await self.rate_limits.acquire(route)
      response = await self._execute_operation(operation, data)
      result = DiscordHTTPResponse(
        status=response.status_code,
        headers=tuple(response.headers.multi_items()),
        body=response.content,
      )
      blocked_until = await self.rate_limits.observe(route, result)
      if blocked_until is not None:
        await self.runtime.nats.publish(
          subjects.HTTP_GLOBAL_LIMIT,
          _GlobalLimit(until=blocked_until).model_dump_json().encode(),
        )
      if not _is_discord_rate_limit(result) or attempt + 1 == self._max_attempts:
        if request.idempotency_key is not None:
          self.rate_limits.complete(request.idempotency_key, result)
        return result
    raise AssertionError("Discord HTTP retry loop did not return.")

  async def _execute_operation(
    self, operation: DiscordHTTPOperation, request: BaseModel
  ) -> httpx2.Response:
    path_value = getattr(request, "path", None)
    query_value = getattr(request, "query", None)
    header_value = getattr(request, "headers", None)
    path_values = (
      path_value.model_dump(mode="json", by_alias=True, exclude_none=True)
      if isinstance(path_value, BaseModel)
      else {}
    )
    path = operation.path
    for field in operation.path_fields:
      path = path.replace("{" + field + "}", quote(str(path_values[field]), safe=""))
    query = (
      query_value.model_dump(mode="json", by_alias=True, exclude_none=True)
      if isinstance(query_value, BaseModel)
      else {}
    )
    headers = (
      {
        name: str(value)
        for name, value in header_value.model_dump(
          mode="json", by_alias=True, exclude_none=True
        ).items()
      }
      if isinstance(header_value, BaseModel)
      else {}
    )
    body = getattr(request, "body", None)
    content_type = getattr(request, "content_type", None)
    if body is None:
      return await self._client().request(
        operation.method, path, params=query, headers=headers
      )
    if content_type == "application/json":
      headers["content-type"] = content_type
      return await self._client().request(
        operation.method,
        path,
        params=query,
        headers=headers,
        content=to_json(_body_mapping(body, mode="json")),
      )
    if content_type == "application/x-www-form-urlencoded":
      headers["content-type"] = content_type
      return await self._client().request(
        operation.method,
        path,
        params=query,
        headers=headers,
        content=urlencode(_body_mapping(body, mode="json"), doseq=True),
      )
    if content_type == "multipart/form-data":
      form, files = _multipart(_body_mapping(body, mode="python"))
      return await self._client().request(
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

  def _client(self) -> httpx2.AsyncClient:
    if self._http is None:
      raise RuntimeError("Discord HTTP worker has not started.")
    return self._http


class DiscordHTTPClient(GeneratedDiscordHTTPClient):
  """Generated Discord API methods, sent to the worker owning each bucket."""

  def __init__(self, runtime: Runtime, *, timeout: float = 60.0) -> None:
    self.runtime = runtime
    self.timeout = timeout

  def workers(self) -> tuple[Registration, ...]:
    return self.runtime.directory.entries(WORKER_KIND)

  async def request(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    operation = HTTP_OPERATIONS[request.operation]
    data = operation.request_model.model_validate_json(to_json(request.data))
    key = partition_key(operation, data)
    payload = request.model_dump_json().encode()
    candidates = rank_workers(key, self.workers())
    if not candidates:
      raise RoutingError("No Discord HTTP worker is running.")
    for worker in candidates:
      try:
        reply = await self.runtime.nats.request(
          subjects.http_worker(worker.id), payload, timeout=self.timeout
        )
      except NoRespondersError:
        # The worker left between our directory update and the call.
        continue
      except NatsTimeoutError as exc:
        raise RequestTimeoutError(f"Discord operation {request.operation!r} timed out.") from exc
      if (reply.headers or {}).get(_STATUS_HEADER) == "error":
        decoded = from_json(reply.data)
        raise RemoteError(
          request.operation,
          str(decoded.get("code", "unknown")),
          str(decoded.get("message", "")),
        )
      return DiscordHTTPResponse.model_validate_json(reply.data)
    raise RoutingError("Every Discord HTTP worker left while routing the request.")

  async def _request_operation(
    self, operation: DiscordOperationId, request: BaseModel
  ) -> BaseModel:
    raw = await self.request(
      DiscordHTTPRequest(
        operation=operation,
        data=request.model_dump(mode="json", by_alias=True),
      )
    )
    definition = HTTP_OPERATIONS[operation]
    body = None
    if raw.body:
      try:
        body = definition.response_body_model.model_validate_json(raw.body)
      except ValueError:
        pass
    return definition.response_model(
      status=raw.status,
      headers=raw.headers,
      body=body,
      raw_body=raw.body,
    )


_MAJOR_PARAMETERS = ("channel_id", "guild_id", "webhook_id", "webhook_token", "interaction_token")


def _major_values(request: BaseModel) -> tuple[str, ...]:
  path = getattr(request, "path", None)
  values = (
    path.model_dump(mode="json", by_alias=True) if isinstance(path, BaseModel) else {}
  )
  return tuple(
    str(values[field])
    for field in _MAJOR_PARAMETERS
    if field in values and values[field] is not None
  )


def route_key(operation: DiscordHTTPOperation, request: BaseModel) -> str:
  """The rate-limit route: operation plus Discord's major parameters."""
  return ":".join((operation.id, *_major_values(request)))


def partition_key(operation: DiscordHTTPOperation, request: BaseModel) -> str:
  """Requests with equal keys share every possible bucket, so one worker owns them.

  Discord buckets are scoped by major parameter, so every route touching one
  channel, guild, or webhook lands on the same worker. Routes without one are
  partitioned by operation.
  """
  major = _major_values(request)
  return ":".join(major) if major else operation.id


def rank_workers(key: str, workers: Sequence[Registration]) -> list[Registration]:
  """Rendezvous (highest random weight) order of workers for a key."""

  def weight(worker: Registration) -> bytes:
    return hashlib.sha256(f"{worker.id}\0{key}".encode()).digest()

  return sorted(workers, key=weight, reverse=True)


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


def _is_discord_rate_limit(response: DiscordHTTPResponse) -> bool:
  return response.status == 429 and any(
    name.lower() == "via" for name, _ in response.headers
  )


def _is_global_rate_limit(
  response: DiscordHTTPResponse, headers: Mapping[str, str]
) -> bool:
  if response.status != 429:
    return False
  if headers.get("x-ratelimit-global") == "true":
    return True
  try:
    body = from_json(response.body)
  except ValueError:
    return False
  return isinstance(body, dict) and body.get("global") is True


__all__ = (
  "DiscordHTTPClient",
  "DiscordHTTPRequest",
  "DiscordHTTPResponse",
  "DiscordHTTPWorker",
  "RateLimits",
  "partition_key",
  "rank_workers",
  "route_key",
)
