import asyncio
import json
from collections import Counter
from collections.abc import Callable

import httpx2

from micro.discord import (
  DiscordHTTPClient,
  DiscordHTTPRequest,
  DiscordHTTPWorker,
  partition_key,
  rank_workers,
)
from micro.discord.http_operations import HTTP_OPERATIONS
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
from micro.runtime import Registration, Runtime

type Responder = Callable[[httpx2.Request], httpx2.Response]


def message(channel: str, content: str = "hello") -> CreateMessageHTTPRequest:
  return CreateMessageHTTPRequest(
    path=CreateMessageParametersPath(channel_id=SnowflakeType(channel)),
    body=CreateMessageRequest(content=content),
  )


def worker(respond: Responder, name: str = "discord.http") -> DiscordHTTPWorker:
  return DiscordHTTPWorker(
    "token",
    name=name,
    transport=httpx2.MockTransport(respond),
    api_url="https://discord.test",
  )


async def wait_for_workers(runtime: Runtime, count: int) -> None:
  await runtime.directory.wait_for(lambda d: len(d.entries("discord.http")) == count)


def test_client_routes_generated_methods_and_retries_rate_limits(nats_url: str) -> None:
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
    async with Runtime(nats_url) as runtime:
      await runtime.add(worker(respond))
      await wait_for_workers(runtime, 1)
      result = await DiscordHTTPClient(runtime).create_message(message("123"))
      assert isinstance(result, CreateMessageHTTPResponse)
      assert result.status == 400
      assert json.loads(result.raw_body) == {"code": 50035, "message": "Invalid form body"}

  asyncio.run(exercise())
  assert len(calls) == 2
  assert calls[0].headers["authorization"] == "Bot token"
  assert calls[0].content == b'{"content":"hello"}'


def test_idempotent_replay_and_binary_bodies(nats_url: str) -> None:
  calls = 0
  sent: list[httpx2.Request] = []

  def respond(request: httpx2.Request) -> httpx2.Response:
    nonlocal calls
    calls += 1
    sent.append(request)
    return httpx2.Response(200, content=b"\x00\xff")

  async def exercise() -> None:
    async with Runtime(nats_url) as runtime:
      await runtime.add(worker(respond))
      await wait_for_workers(runtime, 1)
      client = DiscordHTTPClient(runtime)
      request = DiscordHTTPRequest(
        operation="get_guild",
        data=GetGuildHTTPRequest(
          path=GetGuildParametersPath(guild_id=SnowflakeType("1"))
        ).model_dump(mode="json"),
        idempotency_key="x",
      )
      first = await client.request(request)
      second = await client.request(request)
      assert first == second and first.body == b"\x00\xff"

      upload = UploadApplicationAttachmentHTTPRequest(
        path=UploadApplicationAttachmentParametersPath(application_id=SnowflakeType("1")),
        body=UploadApplicationAttachmentRequest(file=b"\x00binary\xff"),
      )
      await client.upload_application_attachment(upload)

  asyncio.run(exercise())
  assert calls == 2
  assert "multipart/form-data" in sent[-1].headers["content-type"]
  assert b"\x00binary\xff" in sent[-1].content


def test_buckets_stay_on_one_worker_and_move_when_workers_change(nats_url: str) -> None:
  handled: Counter[tuple[str, str]] = Counter()

  def responder(name: str) -> Responder:
    def respond(request: httpx2.Request) -> httpx2.Response:
      channel = request.url.path.split("/")[2]
      handled[(name, channel)] += 1
      return httpx2.Response(200, json={})

    return respond

  async def exercise() -> None:
    runtimes = [Runtime(nats_url) for _ in range(3)]
    for index, runtime in enumerate(runtimes):
      await runtime.add(worker(responder(f"w{index}"), name=f"w{index}"))
    async with Runtime(nats_url) as caller:
      await wait_for_workers(caller, 3)
      client = DiscordHTTPClient(caller)
      channels = [str(1000 + index) for index in range(30)]
      for _ in range(3):
        await asyncio.gather(*(client.create_message(message(c)) for c in channels))
      owners = {channel: {w for (w, c) in handled if c == channel} for channel in channels}
      assert all(len(owner) == 1 for owner in owners.values())
      assert len({next(iter(o)) for o in owners.values()}) == 3

      # Remove one worker: only its channels move, and nothing fails.
      await runtimes[0].drain()
      await runtimes[0].close()
      await wait_for_workers(caller, 2)
      handled.clear()
      await asyncio.gather(*(client.create_message(message(c)) for c in channels))
      moved = {channel for channel, owner in owners.items() if owner == {"w0"}}
      for channel in channels:
        (now,) = {w for (w, c) in handled if c == channel}
        if channel not in moved:
          assert {now} == owners[channel]
        else:
          assert now != "w0"
    for runtime in runtimes[1:]:
      await runtime.drain()
      await runtime.close()

  asyncio.run(exercise())


def test_partitions_follow_major_parameters() -> None:
  operation = HTTP_OPERATIONS["create_message"]
  key = partition_key(operation, message("55"))
  assert key == "55"
  workers = [
    Registration(kind="discord.http", name="w", instance="i", id=str(index))
    for index in range(5)
  ]
  ranked = rank_workers(key, workers)
  assert rank_workers(key, list(reversed(workers))) == ranked
  survivors = [w for w in workers if w.id != ranked[0].id]
  assert rank_workers(key, survivors)[0] == ranked[1]
