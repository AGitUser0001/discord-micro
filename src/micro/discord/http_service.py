import asyncio
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from time import monotonic, time
from typing import Any, Literal, Protocol
from urllib.parse import quote, urlencode

import httpx2
from pydantic import BaseModel, ConfigDict, Field, JsonValue, SecretStr, ValidationError
from pydantic_core import from_json, to_json
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from micro._microservices import (
  DiscordCredential,
  Microservice,
  StoreClient,
  apply_state_atomically,
  request_content_type,
)
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
        if _is_global_rate_limit(response, headers):
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


class StoreRateLimits:
  """Distributed Discord rate limits coordinated through atomic graph mutations."""

  MODULE = "micro.discord.http.rate_limits"

  def __init__(self, store: StoreClient) -> None:
    self.store = store
    self._completed: dict[str, DiscordHTTPResponse] = {}
    self._completed_lock = asyncio.Lock()

  async def acquire(self, route: str) -> None:
    route_id = self._route_id(route)
    while True:
      state = await self._data(
        """
        query RateLimitState($route: ID!, $global: ID!) {
          route: discordHTTPRoute(id: $route) { bucketId }
          global: discordHTTPGlobalLimit(id: $global) { blockedUntil }
        }
        """,
        {"route": route_id, "global": "discord"},
      )
      global_limit = state.get("global")
      if not isinstance(global_limit, dict):
        await self._ensure_global()
        continue
      now = time()
      blocked_until = global_limit.get("blockedUntil")
      if isinstance(blocked_until, int | float) and blocked_until > now:
        await asyncio.sleep(blocked_until - now)
        continue
      route_state = state.get("route")
      if not isinstance(route_state, dict):
        await self._ensure_route(route_id)
        return
      bucket_id = route_state.get("bucketId")
      if not isinstance(bucket_id, str):
        return
      acquired = await self._data(
        """
        mutation Acquire($id: ID!, $now: Float!) {
          bucket: acquireDiscordHTTPBucket(id: $id, now: $now) { id }
        }
        """,
        {"id": bucket_id, "now": now},
      )
      if acquired.get("bucket") is not None:
        return
      bucket = await self._data(
        """
        query Bucket($id: ID!) {
          bucket: discordHTTPBucket(id: $id) { resetAt probeUntil }
        }
        """,
        {"id": bucket_id},
      )
      bucket_state = bucket.get("bucket")
      if not isinstance(bucket_state, dict):
        return
      reset_at = bucket_state.get("resetAt")
      probe_until = bucket_state.get("probeUntil")
      if not isinstance(reset_at, int | float) or not isinstance(
        probe_until, int | float
      ):
        return
      now = time()
      if reset_at <= now:
        if probe_until > now:
          await asyncio.sleep(probe_until - now)
          continue
        claimed = await self._data(
          """
          mutation Claim($id: ID!, $now: Float!, $lease: Float!) {
            bucket: claimExpiredDiscordHTTPBucket(
              id: $id, now: $now, leaseUntil: $lease
            ) { id }
          }
          """,
          {"id": bucket_id, "now": now, "lease": now + 30},
        )
        if claimed.get("bucket") is not None:
          return
        continue
      await asyncio.sleep(reset_at - now)

  async def observe(self, route: str, response: DiscordHTTPResponse) -> None:
    headers = {name.lower(): value for name, value in response.headers}
    retry_after = _retry_after(response, headers)
    if _is_global_rate_limit(response, headers):
      await self._extend_global(time() + retry_after)
      return
    bucket_hash = headers.get("x-ratelimit-bucket")
    if bucket_hash is None:
      return
    route_id = self._route_id(route)
    bucket_id = self._bucket_id(route, bucket_hash)
    await self._ensure_route(route_id)
    await self._ensure_bucket(bucket_id, headers, retry_after)
    await self._data(
      """
      mutation Map($route: ID!, $bucket: ID!) {
        mapDiscordHTTPRoute(id: $route, bucketId: $bucket) { id }
      }
      """,
      {"route": route_id, "bucket": bucket_id},
    )

  async def completed(self, key: str) -> DiscordHTTPResponse | None:
    async with self._completed_lock:
      return self._completed.get(key)

  async def complete(self, key: str, response: DiscordHTTPResponse) -> None:
    async with self._completed_lock:
      if len(self._completed) >= 10_000:
        self._completed.pop(next(iter(self._completed)))
      self._completed[key] = response

  async def _ensure_route(self, route_id: str) -> None:
    await self._create_or_ignore(
      """
      mutation CreateRoute($id: ID!) {
        createDiscordHTTPRoute(id: $id, bucketId: null) { id }
      }
      """,
      {"id": route_id},
    )

  async def _ensure_global(self) -> None:
    await self._create_or_ignore(
      """
      mutation CreateGlobal($id: ID!, $until: Float!) {
        createDiscordHTTPGlobalLimit(id: $id, blockedUntil: $until) { id }
      }
      """,
      {"id": "discord", "until": 0.0},
    )

  async def _extend_global(self, until: float) -> None:
    await self._ensure_global()
    await self._data(
      """
      mutation ExtendGlobal($id: ID!, $until: Float!) {
        extendDiscordHTTPGlobalLimit(id: $id, until: $until) { id }
      }
      """,
      {"id": "discord", "until": until},
    )

  async def _ensure_bucket(
    self, bucket_id: str, headers: Mapping[str, str], retry_after: float
  ) -> None:
    try:
      limit = int(headers.get("x-ratelimit-limit", "1"))
      remaining = int(headers.get("x-ratelimit-remaining", "0"))
      reset_at = (
        float(headers["x-ratelimit-reset"])
        if "x-ratelimit-reset" in headers
        else time()
        + max(
          0.0,
          float(headers.get("x-ratelimit-reset-after", retry_after)),
        )
      )
    except ValueError as exc:
      raise ValueError("Discord returned invalid rate-limit headers.") from exc
    values: dict[str, JsonValue] = {
      "id": bucket_id,
      "limit": max(1, limit),
      "remaining": max(0, remaining),
      "reset": reset_at,
      "probe": 0.0,
    }
    created = await self._create_or_ignore(
      """
      mutation CreateBucket(
        $id: ID!, $limit: Int!, $remaining: Int!, $reset: Float!, $probe: Float!
      ) {
        createDiscordHTTPBucket(
          id: $id, limit: $limit, remaining: $remaining,
          resetAt: $reset, probeUntil: $probe
        ) { id }
      }
      """,
      values,
    )
    if created:
      return
    await self._data(
      """
      mutation AdvanceBucket($id: ID!, $limit: Int!, $remaining: Int!, $reset: Float!) {
        advanceDiscordHTTPBucket(
          id: $id, limit: $limit, remaining: $remaining, resetAt: $reset
        ) { id }
      }
      """,
      values,
    )
    await self._data(
      """
      mutation ReduceBucket($id: ID!, $remaining: Int!, $reset: Float!) {
        reduceDiscordHTTPBucket(id: $id, remaining: $remaining, resetAt: $reset) { id }
      }
      """,
      values,
    )

  async def _create_or_ignore(
    self, query: str, variables: Mapping[str, JsonValue]
  ) -> bool:
    response = await self.store.execute(query, variables=variables, module=self.MODULE)
    return not response.get("errors")

  async def _data(
    self, query: str, variables: Mapping[str, JsonValue]
  ) -> dict[str, Any]:
    response = await self.store.execute(query, variables=variables, module=self.MODULE)
    if errors := response.get("errors"):
      raise RuntimeError(f"Discord rate-limit store rejected an operation: {errors}")
    data = response.get("data")
    if not isinstance(data, dict):
      raise TypeError("Discord rate-limit store omitted GraphQL data.")
    return data

  def _route_id(self, route: str) -> str:
    return hashlib.sha256(route.encode()).hexdigest()

  def _bucket_id(self, route: str, bucket_hash: str) -> str:
    major_parameters = route.partition(":")[2]
    return hashlib.sha256(f"{bucket_hash}\0{major_parameters}".encode()).hexdigest()


class DiscordHTTPWorker(Microservice):
  """Queue worker that validates and executes generated Discord operations."""

  def __init__(
    self,
    token: str | None = None,
    *,
    api_url: str = "https://discord.com/api/v10",
    transport: httpx2.AsyncBaseTransport | None = None,
    coordinator: RateLimitCoordinator | None = None,
    max_attempts: int = 4,
  ) -> None:
    if token == "":
      raise ValueError("token cannot be empty.")
    if not 1 <= max_attempts <= 10:
      raise ValueError("max_attempts must be between 1 and 10.")
    self.queue = QueueClient(transport=transport)
    self.store = StoreClient(transport=transport)
    self._http = httpx2.AsyncClient(
      base_url=api_url,
      transport=transport,
      headers={"user-agent": "DiscordBot (Micro)"},
    )
    self._coordinator = coordinator or StoreRateLimits(self.store)
    self._max_attempts = max_attempts
    self._consumer: asyncio.Task[None] | None = None
    self._topology_ready = asyncio.Event()
    self._credential_ready = asyncio.Event()
    self._credential_revision = -1
    self._credential_token: str | None = None
    super().__init__("discord.http")
    self.add_route(
      "/discord/credential",
      self._credential_endpoint,
      methods=("POST",),
      name="discord:http:credential",
    )
    if token is not None:
      self._apply_credential(DiscordCredential(token=SecretStr(token), revision=0))

  def apply_state(self, state: JsonValue) -> None:
    apply_state_atomically((self.queue, self.store), state)
    self._topology_ready.set()

  @property
  def component_ready(self) -> bool:
    return (
      self.queue.state_revision >= 0
      and self.store.state_revision >= 0
      and self._credential_revision >= 0
    )

  def _apply_credential(self, credential: DiscordCredential) -> None:
    token = credential.token.get_secret_value()
    if credential.revision < self._credential_revision:
      raise ValueError("Discord credential revision is stale.")
    if (
      credential.revision == self._credential_revision
      and self._credential_token is not None
      and token != self._credential_token
    ):
      raise ValueError("A revision cannot identify two Discord credentials.")
    self._http.headers["authorization"] = f"Bot {token}"
    self._credential_token = token
    self._credential_revision = credential.revision
    self._credential_ready.set()

  async def _credential_endpoint(self, request: Request) -> Response:
    if request_content_type(request) != "application/json":
      return JSONResponse(
        {"detail": "Credential updates require application/json."}, status_code=415
      )
    try:
      credential = DiscordCredential.model_validate_json(await request.body())
      self._apply_credential(credential)
    except ValidationError as exc:
      return JSONResponse(
        {
          "detail": "Invalid Discord credential.",
          "errors": exc.errors(include_url=False),
        },
        status_code=422,
      )
    except ValueError as exc:
      return JSONResponse({"detail": str(exc)}, status_code=409)
    return Response(status_code=204)

  async def start(self) -> None:
    self._consumer = asyncio.create_task(self._consume(), name="micro.discord.http")

  async def close(self) -> None:
    if self._consumer is not None:
      self._consumer.cancel()
      await asyncio.gather(self._consumer, return_exceptions=True)
      self._consumer = None
    await self._http.aclose()
    await self.queue.aclose()
    await self.store.aclose()

  async def execute(self, request: DiscordHTTPRequest) -> DiscordHTTPResponse:
    if self._credential_revision < 0:
      raise RuntimeError("Discord credential is not configured.")
    if request.idempotency_key is not None:
      completed = await self._coordinator.completed(request.idempotency_key)
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
      if not _is_discord_rate_limit(result) or attempt + 1 == self._max_attempts:
        if request.idempotency_key is not None:
          await self._coordinator.complete(request.idempotency_key, result)
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
    await self._credential_ready.wait()
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


class DiscordHTTPClient(GeneratedDiscordHTTPClient):
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

  async def aclose(self) -> None:
    await self.queue.aclose()


def _route_key(operation: DiscordHTTPOperation, request: BaseModel) -> str:
  path = getattr(request, "path", None)
  values = (
    path.model_dump(mode="json", by_alias=True) if isinstance(path, BaseModel) else {}
  )
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
  "DISCORD_HTTP_CHANNEL",
  "DiscordHTTPClient",
  "DiscordHTTPRequest",
  "DiscordHTTPResponse",
  "DiscordHTTPWorker",
  "MemoryRateLimits",
  "RateLimitCoordinator",
  "StoreRateLimits",
)
