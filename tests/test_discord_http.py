import asyncio
import json

import httpx2

from micro.discord import (
  DiscordHTTPClient,
  DiscordHTTPRequest,
  DiscordHTTPResponse,
  DiscordHTTPWorker,
)
from micro.discord.models.http import (
  DiscordHTTPCreateMessageInput,
  DiscordHTTPGetGuildInput,
  DiscordHTTPUploadApplicationAttachmentInput,
  DiscordHTTPUploadApplicationAttachmentMultipartFormDataBody,
  MessageCreateRequest,
  SnowflakeType,
)
from micro.queue import QueueClient


def test_discord_http_retries_rate_limits_and_preserves_response() -> None:
  calls: list[httpx2.Request] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    calls.append(request)
    if len(calls) == 1:
      return httpx2.Response(
        429,
        headers={"retry-after": "0", "x-ratelimit-global": "true"},
        json={"retry_after": 0, "global": True},
      )
    return httpx2.Response(
      400,
      headers={"x-ratelimit-bucket": "messages", "x-ratelimit-remaining": "1"},
      json={"code": 50035, "message": "Invalid form body"},
    )

  async def exercise() -> None:
    worker = DiscordHTTPWorker(
      "token", transport=httpx2.MockTransport(respond), api_url="https://discord.test"
    )
    try:
      response = await worker.execute(
        DiscordHTTPRequest(
          operation="create_message",
          data=DiscordHTTPCreateMessageInput(
            channel_id=SnowflakeType("123"),
            body=MessageCreateRequest(content="hello"),
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


def test_discord_http_binary_wire_format_and_idempotent_replay() -> None:
  calls = 0

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal calls
    calls += 1
    return httpx2.Response(200, content=b"\x00\xff")

  async def exercise() -> None:
    worker = DiscordHTTPWorker("token", transport=httpx2.MockTransport(respond))
    request = DiscordHTTPRequest(
      operation="get_guild",
      data=DiscordHTTPGetGuildInput(guild_id=SnowflakeType("1")).model_dump(
        mode="json"
      ),
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

  async def exercise() -> None:
    queue = QueueClient(transport=httpx2.MockTransport(respond))
    queue.apply_state(
      {
        "revision": 0,
        "queues": [{"id": "queue", "base_url": "https://queue.test"}],
      }
    )
    client = DiscordHTTPClient(queue)
    try:
      await client.create_message(
        DiscordHTTPCreateMessageInput(
          channel_id=SnowflakeType("123"),
          body=MessageCreateRequest(content="hello"),
        )
      )
    finally:
      await client.aclose()

  asyncio.run(exercise())
  assert received is not None
  assert received.operation == "create_message"
  assert received.data["channel_id"] == "123"


def test_generated_multipart_operation_preserves_binary_files() -> None:
  sent: httpx2.Request | None = None

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal sent
    sent = request
    return httpx2.Response(200, json={})

  async def exercise() -> None:
    worker = DiscordHTTPWorker("token", transport=httpx2.MockTransport(respond))
    data = DiscordHTTPUploadApplicationAttachmentInput(
      application_id=SnowflakeType("1"),
      body=DiscordHTTPUploadApplicationAttachmentMultipartFormDataBody(
        file=b"\x00binary\xff"
      ),
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
