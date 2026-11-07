import asyncio
import hashlib
import inspect
import json
import logging
import os
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from time import monotonic, time
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import quote, urlencode

from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import NoRespondersError
from nats.errors import TimeoutError as NatsTimeoutError
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic_core import from_json, to_json

from micro import subjects
from micro.errors import MicroError, RemoteError, RequestTimeoutError, RoutingError
from micro.runtime import Component, Presence, Registration, Runtime

from .http_operations import (
  HTTP_OPERATIONS,
  DiscordHTTPOperation,
  DiscordOperationId,
  GeneratedDiscordHTTPClient,
)

if TYPE_CHECKING:
  import httpx2  # Loaded at runtime only by the worker.

  from micro.discord.api import DiscordAPI

logger = logging.getLogger("micro")

WORKER_KIND = "discord.http"
_STATUS_HEADER = "Micro-Status"


class DiscordHTTPFile(BaseModel):
  """A file to upload with a request: one part of a multipart body."""

  model_config = ConfigDict(
    frozen=True, ser_json_bytes="base64", val_json_bytes="base64"
  )
  field: str
  """The multipart field: `files[0]`, `file`, ..."""
  filename: str
  data: bytes
  content_type: str | None = None


class DiscordHTTPRequest(BaseModel):
  """One generated Discord OpenAPI operation invocation."""

  model_config = ConfigDict(
    extra="ignore", frozen=True, ser_json_bytes="base64", val_json_bytes="base64"
  )
  operation: DiscordOperationId
  data: dict[str, JsonValue]
  idempotency_key: str | None = None
  files: tuple[DiscordHTTPFile, ...] = ()
  """Uploads: the request is sent as multipart, the rest of `data`'s body as JSON."""
  reason: str | None = None
  """The audit log reason (sent as X-Audit-Log-Reason)."""


class DiscordHTTPResponse(BaseModel):
  """Unmodified Discord response status, headers, and body."""

  model_config = ConfigDict(
    extra="ignore", frozen=True, ser_json_bytes="base64", val_json_bytes="base64"
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
    """Wait until the route's bucket and the global limit allow another request."""
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
    """Pause every route until the given wall-clock time."""
    self._global_reset = max(self._global_reset, monotonic() + wall_clock - time())

  def completed(self, key: str) -> DiscordHTTPResponse | None:
    """The remembered response for an idempotency key, or None."""
    return self._completed.get(key)

  def complete(self, key: str, response: DiscordHTTPResponse) -> None:
    """Remember the response to an idempotency key."""
    if len(self._completed) >= 10_000:
      self._completed.pop(next(iter(self._completed)))
    self._completed[key] = response


@dataclass(frozen=True, slots=True)
class HTTPEvent:
  """One Discord request attempt, as given to `DiscordHTTPWorker.hook` callbacks."""

  operation: str
  route: str
  attempt: int  # 1 for the first try
  status: int | None  # None when the request never got an answer
  seconds: float
  error: BaseException | None = None
  rate_limited: bool = False


HTTPHook = Callable[[HTTPEvent], Awaitable[None] | None]

type RewriteHook = Callable[
  [DiscordHTTPRequest], Awaitable[DiscordHTTPRequest | None] | DiscordHTTPRequest | None
]
"""Given a request about to run: return a changed copy, or None to leave it."""


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
    api_url: str | None = None,
    transport: httpx2.AsyncBaseTransport | None = None,
    max_attempts: int = 4,
    concurrency: int = 256,
  ) -> None:
    token = token if token is not None else os.environ.get("DISCORD_TOKEN")
    if not token:
      raise ValueError("A Discord token is required (argument or DISCORD_TOKEN).")
    if max_attempts < 1:
      raise ValueError("max_attempts must be at least 1.")
    super().__init__(name)
    self._token = token
    self._api_url = (
      api_url or os.environ.get("DISCORD_API_URL") or "https://discord.com/api/v10"
    )
    self._transport = transport
    self._max_attempts = max_attempts
    self._slots = asyncio.Semaphore(concurrency)
    self.rate_limits = RateLimits()
    self._hooks: list[HTTPHook] = []
    self._rewriters: list[RewriteHook] = []
    self._http: httpx2.AsyncClient | None = None
    self._subscriptions: list[Subscription] = []
    self._presence: Presence | None = None
    self.address = subjects.token(os.urandom(8).hex())

  async def on_start(self) -> None:
    """Create the HTTP client and subscribe to requests and global-limit announcements."""
    import httpx2

    self._http = httpx2.AsyncClient(
      base_url=self._api_url,
      transport=self._transport,
      headers={
        "user-agent": "DiscordBot (Micro)",
        "authorization": f"Bot {self._token}",
      },
    )
    nats = self.runtime.nats
    self._subscriptions = [
      await nats.subscribe(subjects.http_worker(self.address), cb=self._on_request),
      await nats.subscribe(subjects.HTTP_GLOBAL_LIMIT, cb=self._on_global_limit),
    ]
    self._presence = await self.runtime.register(self, id=self.address)

  async def on_drain(self) -> None:
    # Leave the partition first so callers re-route, then finish what arrived.
    """Leave presence so callers re-route, then finish what arrived."""
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    await self._unsubscribe()

  async def on_close(self) -> None:
    """Unsubscribe and close the HTTP client."""
    if self._presence is not None:
      await self.runtime.unregister(self._presence)
      self._presence = None
    await self._unsubscribe()
    if self._http is not None:
      await self._http.aclose()
      self._http = None

  def hook(self, callback: HTTPHook) -> Callable[[], None]:
    """Call `callback(event)` after every Discord request this worker makes.

    One call per attempt (a retry after a 429 is its own event). The callback may
    be sync or async; its errors are logged and never affect the request. Hooks
    are local to this worker. With none registered the request path does no extra
    work. Returns a function that removes the hook.
    """
    self._hooks.append(callback)
    return lambda: self._hooks.remove(callback) if callback in self._hooks else None

  def rewrite(self, callback: RewriteHook) -> Callable[[], None]:
    """Change or refuse every request before this worker sends it.

    `callback(request)` gets the `DiscordHTTPRequest` (operation, data, files,
    reason) and returns a changed copy (`request.model_copy(update=...)`), or None
    to leave it. Rewriters run in the order added, each seeing the previous one's
    result, before the request is validated and before its rate-limit route is
    chosen, so changing `operation` or the ids in `data` is safe. Raise to refuse:
    a `ValueError` reaches the caller as `invalid_input`, anything else as
    `handler_failed`, and nothing is sent. They run once per request, not per
    retry, and a request answered from its idempotency key is not rewritten.
    Local to this worker: run the same rewriters on every worker. Returns a
    function that removes it.
    """
    self._rewriters.append(callback)
    return lambda: (
      self._rewriters.remove(callback) if callback in self._rewriters else None
    )

  async def _rewritten(self, request: DiscordHTTPRequest) -> DiscordHTTPRequest:
    for callback in tuple(self._rewriters):
      outcome = callback(request)
      if inspect.isawaitable(outcome):
        outcome = await outcome
      if outcome is not None:
        request = outcome
    return request

  async def _notify(self, event: HTTPEvent) -> None:
    for callback in tuple(self._hooks):
      try:
        outcome = callback(event)
        if inspect.isawaitable(outcome):
          await outcome
      except Exception:
        logger.exception("HTTP hook failed")

  async def _unsubscribe(self) -> None:
    subscriptions, self._subscriptions = self._subscriptions, []
    for subscription in subscriptions:
      try:
        await subscription.drain()
      except Exception:
        logger.debug("HTTP worker subscription drain failed", exc_info=True)

  async def _on_global_limit(self, message: Msg) -> None:
    try:
      self.rate_limits.block_globally_until(
        _GlobalLimit.model_validate_json(message.data).until
      )
    except ValueError:
      logger.warning("Ignoring an invalid global rate-limit announcement")

  async def _on_request(self, message: Msg) -> None:
    await self._slots.acquire()
    task = asyncio.create_task(self._answer(message))
    task.add_done_callback(lambda _: self._slots.release())

  async def _answer(self, message: Msg) -> None:
    async with self.tracked():
      try:
        request = DiscordHTTPRequest.model_validate_json(
          await self.runtime.payload(message)
        )
        body = (await self.execute(request)).model_dump_json().encode()
        headers = {_STATUS_HEADER: "ok"}
      except Exception as exc:
        logger.exception("Discord HTTP request failed")
        code = "invalid_input" if isinstance(exc, ValueError) else "handler_failed"
        body = json.dumps(
          {"code": code, "message": f"{type(exc).__name__}: {exc}"}
        ).encode()
        headers = {_STATUS_HEADER: "error"}
      await self.runtime.respond(message, body, headers=headers)

  async def execute(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    """Run one request: rewrite, validate, wait for the bucket, send, observe, and retry a Discord 429."""
    if request.idempotency_key is not None:
      completed = self.rate_limits.completed(request.idempotency_key)
      if completed is not None:
        return completed
    if self._rewriters:
      request = await self._rewritten(request)
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
      started = monotonic()
      try:
        response = await self._execute_operation(
          operation, data, request.files, request.reason
        )
      except Exception as exc:
        if self._hooks:
          await self._notify(
            HTTPEvent(
              operation.id, route, attempt + 1, None, monotonic() - started, exc
            )
          )
        raise
      result = DiscordHTTPResponse(
        status=response.status_code,
        headers=tuple(response.headers.multi_items()),
        body=response.content,
      )
      if self._hooks:
        await self._notify(
          HTTPEvent(
            operation.id,
            route,
            attempt + 1,
            result.status,
            monotonic() - started,
            None,
            _is_discord_rate_limit(result),
          )
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
    self,
    operation: DiscordHTTPOperation,
    request: BaseModel,
    files: Sequence[DiscordHTTPFile] = (),
    reason: str | None = None,
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
    if reason is not None:
      headers["X-Audit-Log-Reason"] = quote(reason, safe="")
    body = getattr(request, "body", None)
    content_type = getattr(request, "content_type", None)
    if files:
      content_type = "multipart/form-data"
    if body is None and not files:
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
      form, parts = _multipart(operation, body, files)
      return await self._client().request(
        operation.method,
        path,
        params=query,
        headers=headers,
        data=form,
        files=parts,
      )
    raise ValueError(
      f"Operation {operation.id!r} has unsupported content type {content_type!r}."
    )

  def _client(self) -> httpx2.AsyncClient:
    if self._http is None:
      raise RuntimeError("Discord HTTP worker has not started.")
    return self._http


class DiscordAPIError(MicroError):
  """Discord answered an operation with an error status."""

  def __init__(self, operation: str, response: DiscordHTTPResponse) -> None:
    self.operation = operation
    self.status = response.status
    self.response = response
    try:
      self.body: JsonValue | str | None = (
        from_json(response.body) if response.body else None
      )
    except ValueError:
      self.body = response.body.decode(errors="replace")
    super().__init__(
      f"Discord rejected {operation} with HTTP {response.status}: {self.body}"
    )


class DiscordHTTPClient(GeneratedDiscordHTTPClient):
  """Generated Discord API methods, sent to the worker owning each bucket."""

  def __init__(self, runtime: Runtime, *, timeout: float = 60.0) -> None:
    self.runtime = runtime
    self.timeout = timeout

  @property
  def api(self) -> DiscordAPI:
    """Every operation as a method with plain arguments (see `micro.discord.api`)."""
    from micro.discord.api import DiscordAPI

    return DiscordAPI(self)

  def workers(self) -> tuple[Registration, ...]:
    """The live HTTP workers."""
    return self.runtime.directory.entries(WORKER_KIND)

  async def request(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    """Send a validated request to the worker owning its bucket and return the raw response."""
    operation = HTTP_OPERATIONS[request.operation]
    data = operation.request_model.model_validate_json(to_json(request.data))
    key = partition_key(operation, data)
    payload = request.model_dump_json().encode()
    candidates = rank_workers(key, self.workers())
    if not candidates:
      raise RoutingError("No Discord HTTP worker is running.")
    for worker in candidates:
      try:
        reply = await self.runtime.request(
          subjects.http_worker(worker.id), payload, timeout=self.timeout
        )
      except NoRespondersError:
        # The worker left between our directory update and the call.
        continue
      except NatsTimeoutError as exc:
        raise RequestTimeoutError(
          f"Discord operation {request.operation!r} timed out."
        ) from exc
      if (reply.headers or {}).get(_STATUS_HEADER) == "error":
        decoded = from_json(reply.data)
        raise RemoteError(
          request.operation,
          str(decoded.get("code", "unknown")),
          str(decoded.get("message", "")),
        )
      return DiscordHTTPResponse.model_validate_json(reply.data)
    raise RoutingError("Every Discord HTTP worker left while routing the request.")

  async def call(
    self,
    operation: DiscordOperationId,
    *,
    path: dict[str, JsonValue] | None = None,
    query: dict[str, JsonValue] | None = None,
    body: JsonValue = None,
  ) -> Any:
    """Run an operation from plain JSON parts; return the decoded body.

    Raises `DiscordAPIError` for error statuses. The worker validates the parts
    against the generated request model.
    """
    data: dict[str, JsonValue] = {}
    if path is not None:
      data["path"] = path
    if query is not None:
      data["query"] = query
    if body is not None:
      data["body"] = body
    response = await self.request(DiscordHTTPRequest(operation=operation, data=data))
    if response.status >= 400:
      raise DiscordAPIError(operation, response)
    return from_json(response.body) if response.body else None

  async def _request_operation(
    self,
    operation: DiscordOperationId,
    request: BaseModel,
    files: Sequence[DiscordHTTPFile] = (),
    reason: str | None = None,
  ) -> BaseModel:
    raw = await self.request(
      DiscordHTTPRequest(
        operation=operation,
        data=request.model_dump(mode="json", by_alias=True, exclude_unset=True),
        files=tuple(files),
        reason=reason,
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


_MAJOR_PARAMETERS = (
  "channel_id",
  "guild_id",
  "webhook_id",
  "webhook_token",
  "interaction_token",
)


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


def _multipart(
  operation: DiscordHTTPOperation,
  body: BaseModel | Mapping[str, object] | None,
  files: Sequence[DiscordHTTPFile],
) -> tuple[dict[str, str], dict[str, tuple[str, bytes] | tuple[str, bytes, str]]]:
  """The form fields and file parts of a multipart request.

  A message-like operation (it also takes JSON) sends everything but the files as
  `payload_json`, the way Discord reads uploads; the others (stickers, invites,
  attachments) send each field as a plain form field. Bytes left in the body are files
  named after their field; `files` carry real file names and types.
  """
  mapping = _body_mapping(body, mode="python") if body is not None else {}
  parts: dict[str, tuple[str, bytes] | tuple[str, bytes, str]] = {}
  for item in files:
    mapping.pop(item.field, None)
    parts[item.field] = (
      (item.filename, item.data, item.content_type)
      if item.content_type
      else (item.filename, item.data)
    )
  fields: dict[str, object] = {}
  for name, value in mapping.items():
    if isinstance(value, bytes):
      parts[name] = (name, value)
    else:
      fields[name] = value
  if "application/json" in operation.content_types:
    return {"payload_json": to_json(fields).decode()}, parts
  return {
    name: value
    if isinstance(value, str)
    else json.dumps(value, default=str, separators=(",", ":"))
    for name, value in fields.items()
  }, parts


def _body_mapping(
  body: BaseModel | Mapping[str, object] | None, *, mode: Literal["json", "python"]
) -> dict[str, object]:
  if isinstance(body, BaseModel):
    # What was set, so an explicit null (clearing a topic, say) is sent as null.
    return body.model_dump(mode=mode, by_alias=True, exclude_unset=True)
  if isinstance(body, Mapping):
    return dict(body)
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
  "DiscordAPIError",
  "DiscordHTTPClient",
  "DiscordHTTPRequest",
  "DiscordHTTPResponse",
  "DiscordHTTPWorker",
  "RateLimits",
  "partition_key",
  "rank_workers",
  "route_key",
)
