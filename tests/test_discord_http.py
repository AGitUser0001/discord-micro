import asyncio
import json

import httpx2

from micro.discord import DiscordHTTPRequest, DiscordHTTPWorker


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
          method="POST",
          path="/channels/123/messages",
          headers=(("content-type", "application/json"),),
          body=b'{"content":"hello"}',
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
      method="POST", path="/webhooks/1/token", body=b"\x00\xff", idempotency_key="x"
    )
    encoded = request.model_dump_json()
    decoded = DiscordHTTPRequest.model_validate_json(encoded)
    assert decoded.body == b"\x00\xff"
    try:
      first = await worker.execute(decoded)
      second = await worker.execute(decoded)
    finally:
      await worker.close()
    assert first == second

  asyncio.run(exercise())
  assert calls == 1
