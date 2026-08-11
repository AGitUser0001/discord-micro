import asyncio
import json
from typing import Any

import httpx2
from starlette.testclient import TestClient

from micro._microservices import StoreClient
from micro.discord import (
  DiscordHTTPClient,
  DiscordHTTPRequest,
  DiscordHTTPResponse,
  DiscordHTTPWorker,
  MemoryRateLimits,
  StoreRateLimits,
)
from micro.discord.models.http import (
  CreateMessageParametersPath,
  CreateMessageRequest,
  GetGuildParametersPath,
  SnowflakeType,
  UploadApplicationAttachmentParametersPath,
  UploadApplicationAttachmentRequest,
)
from micro.discord.models.http_requests import (
  CreateMessageHTTPRequest,
  CreateMessageHTTPResponse,
  GetGuildHTTPRequest,
  UploadApplicationAttachmentHTTPRequest,
)
from micro.queue import QueueClient


class _RateLimitStore(StoreClient):
  def __init__(self) -> None:
    self.calls: list[tuple[str, dict[str, Any]]] = []
    self.route: dict[str, Any] | None = None
    self.global_limit: dict[str, Any] | None = {"blockedUntil": 0.0}
    self.acquire_result: dict[str, Any] | None = {"id": "bucket"}

  async def execute(
    self,
    query: str,
    *,
    variables=None,
    operation_name=None,
    module=None,
  ) -> dict[str, Any]:
    values = dict(variables or {})
    self.calls.append((query, values))
    if "RateLimitState" in query:
      return {"data": {"route": self.route, "global": self.global_limit}}
    if "Acquire(" in query:
      return {"data": {"bucket": self.acquire_result}}
    if "CreateRoute" in query:
      self.route = {"bucketId": None}
    if "Map(" in query:
      self.route = {"bucketId": values["bucket"]}
    return {"data": {}}


def test_discord_http_retries_rate_limits_and_preserves_response() -> None:
  calls: list[httpx2.Request] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    calls.append(request)
    if len(calls) == 1:
      return httpx2.Response(
        429,
        headers={"retry-after": "0", "x-ratelimit-global": "true", "via": "1.1"},
        json={"retry_after": 0, "global": True},
      )
    return httpx2.Response(
      400,
      headers={"x-ratelimit-bucket": "messages", "x-ratelimit-remaining": "1"},
      json={"code": 50035, "message": "Invalid form body"},
    )

  async def exercise() -> None:
    worker = DiscordHTTPWorker(
      "token",
      transport=httpx2.MockTransport(respond),
      api_url="https://discord.test",
      coordinator=MemoryRateLimits(),
    )
    try:
      response = await worker.execute(
        DiscordHTTPRequest(
          operation="create_message",
          data=CreateMessageHTTPRequest(
            path=CreateMessageParametersPath(channel_id=SnowflakeType("123")),
            body=CreateMessageRequest(content="hello"),
          ).model_dump(mode="json", by_alias=True),
          idempotency_key="message-1",
        )
      )
    finally:
      await worker.close()
    assert response.status == 400
    assert json.loads(response.body) == {
      "code": 50035,
      "message": "Invalid form body",
    }

  asyncio.run(exercise())
  assert len(calls) == 2
  assert calls[0].headers["authorization"] == "Bot token"
  assert calls[0].content == b'{"content":"hello"}'


def test_discord_http_credential_endpoint_rotates_new_requests() -> None:
  calls: list[httpx2.Request] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    calls.append(request)
    return httpx2.Response(200, json={"id": "123", "name": "guild"})

  worker = DiscordHTTPWorker(
    "old",
    transport=httpx2.MockTransport(respond),
    api_url="https://discord.test",
    coordinator=MemoryRateLimits(),
  )
  with TestClient(worker) as client:
    rotated = client.post("/discord/credential", json={"token": "new", "revision": 1})
    stale = client.post("/discord/credential", json={"token": "stale", "revision": 0})
    response = asyncio.run(
      worker.execute(
        DiscordHTTPRequest(
          operation="get_guild",
          data=GetGuildHTTPRequest(
            path=GetGuildParametersPath(guild_id=SnowflakeType("123"))
          ).model_dump(mode="json", by_alias=True),
        )
      )
    )

  assert rotated.status_code == 204
  assert stale.status_code == 409
  assert response.status == 200
  assert calls[-1].headers["authorization"] == "Bot new"


def test_discord_http_binary_wire_format_and_idempotent_replay() -> None:
  calls = 0

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal calls
    calls += 1
    return httpx2.Response(200, content=b"\x00\xff")

  async def exercise() -> None:
    worker = DiscordHTTPWorker(
      "token", transport=httpx2.MockTransport(respond), coordinator=MemoryRateLimits()
    )
    request = DiscordHTTPRequest(
      operation="get_guild",
      data=GetGuildHTTPRequest(
        path=GetGuildParametersPath(guild_id=SnowflakeType("1"))
      ).model_dump(mode="json"),
      idempotency_key="x",
    )
    encoded = request.model_dump_json()
    decoded = DiscordHTTPRequest.model_validate_json(encoded)
    assert decoded == request
    try:
      first = await worker.execute(decoded)
      second = await worker.execute(decoded)
    finally:
      await worker.close()
    assert first == second

  asyncio.run(exercise())
  assert calls == 1


def test_generated_physical_method_uses_the_operation_registry() -> None:
  received: DiscordHTTPRequest | None = None

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal received
    received = DiscordHTTPRequest.model_validate_json(request.read())
    response = DiscordHTTPResponse(status=200, headers=(), body=b"{}")
    return httpx2.Response(200, content=response.model_dump_json().encode())

  async def exercise() -> CreateMessageHTTPResponse:
    queue = QueueClient(transport=httpx2.MockTransport(respond))
    queue.apply_state(
      {
        "revision": 0,
        "queues": [{"id": "queue", "base_url": "https://queue.test"}],
      }
    )
    client = DiscordHTTPClient(queue)
    try:
      return await client.create_message(
        CreateMessageHTTPRequest(
          path=CreateMessageParametersPath(channel_id=SnowflakeType("123")),
          body=CreateMessageRequest(content="hello"),
        )
      )
    finally:
      await client.aclose()

  result = asyncio.run(exercise())
  assert isinstance(result, CreateMessageHTTPResponse)
  assert result.status == 200
  assert result.raw_body == b"{}"
  assert received is not None
  assert received.operation == "create_message"
  assert received.data["path"] == {"channel_id": "123"}


def test_generated_multipart_operation_preserves_binary_files() -> None:
  sent: httpx2.Request | None = None

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal sent
    sent = request
    return httpx2.Response(200, json={})

  async def exercise() -> None:
    worker = DiscordHTTPWorker(
      "token", transport=httpx2.MockTransport(respond), coordinator=MemoryRateLimits()
    )
    data = UploadApplicationAttachmentHTTPRequest(
      path=UploadApplicationAttachmentParametersPath(application_id=SnowflakeType("1")),
      body=UploadApplicationAttachmentRequest(file=b"\x00binary\xff"),
    )
    try:
      await worker.execute(
        DiscordHTTPRequest(
          operation="upload_application_attachment",
          data=data.model_dump(mode="json", by_alias=True),
        )
      )
    finally:
      await worker.close()

  asyncio.run(exercise())
  assert sent is not None
  assert "multipart/form-data" in sent.headers["content-type"]
  assert b"\x00binary\xff" in sent.content


def test_store_rate_limits_map_discovered_buckets_and_acquire_capacity() -> None:
  async def exercise() -> _RateLimitStore:
    store = _RateLimitStore()
    coordinator = StoreRateLimits(store)
    response = DiscordHTTPResponse(
      status=200,
      headers=(
        ("x-ratelimit-bucket", "messages"),
        ("x-ratelimit-limit", "5"),
        ("x-ratelimit-remaining", "4"),
        ("x-ratelimit-reset", "2000000000"),
      ),
      body=b"{}",
    )
    await coordinator.observe("create_message:123", response)
    assert store.route is not None
    assert isinstance(store.route["bucketId"], str)
    await coordinator.acquire("create_message:123")
    return store

  store = asyncio.run(exercise())
  queries = "\n".join(query for query, _ in store.calls)
  assert "CreateBucket" in queries
  assert "Map(" in queries
  assert "Acquire(" in queries


def test_store_rate_limits_extend_the_shared_global_gate() -> None:
  async def exercise() -> _RateLimitStore:
    store = _RateLimitStore()
    coordinator = StoreRateLimits(store)
    await coordinator.observe(
      "create_message:123",
      DiscordHTTPResponse(
        status=429,
        headers=(("via", "1.1"), ("retry-after", "2")),
        body=b'{"retry_after":2,"global":true}',
      ),
    )
    return store

  store = asyncio.run(exercise())
  extend = next(
    variables for query, variables in store.calls if "ExtendGlobal" in query
  )
  assert isinstance(extend["until"], float)
