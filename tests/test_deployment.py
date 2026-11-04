"""Whole-deployment behavior: zero store, the HTTP bridge, and the supervisor."""

import asyncio
import json
import os
import signal
import sys
import textwrap
from pathlib import Path
from typing import Any

import httpx2
from test_gateway import SESSIONS, FakeShard, eventually

from micro import subjects
from micro.discord import DiscordHTTPClient, DiscordHTTPWorker
from micro.discord.models.http import (
  CreateMessageParametersPath,
  CreateMessageRequest,
  SnowflakeType,
)
from micro.discord.models.http_requests import CreateMessageHTTPRequest
from micro.gateway import GatewayWorker
from micro.runtime import Runtime
from micro.schemas import events
from micro.service import RequestSchema, Service


def test_gateway_http_worker_and_service_run_without_a_store(nats_url: str) -> None:
  sent: list[httpx2.Request] = []

  def discord(request: httpx2.Request) -> httpx2.Response:
    sent.append(request)
    return httpx2.Response(200, json={"id": "1"})

  bot = Service("pong")

  @bot.listen(events.MESSAGE_CREATE)
  async def on_message(message: Any) -> None:
    if message.content == "!ping":
      await DiscordHTTPClient(bot.runtime).create_message(
        CreateMessageHTTPRequest(
          path=CreateMessageParametersPath(
            channel_id=SnowflakeType(message.channel_id)
          ),
          body=CreateMessageRequest(content="pong"),
        )
      )

  async def exercise() -> None:
    SESSIONS.clear()
    gateway = GatewayWorker(
      "token", intents=0, lease_ttl=3, max_concurrency=16, session_factory=FakeShard
    )
    http = DiscordHTTPWorker(
      "token", transport=httpx2.MockTransport(discord), api_url="https://discord.test"
    )
    async with Runtime(nats_url) as runtime:
      await runtime.add(http, bot, gateway)
      await eventually(lambda: gateway.publishing_shards == (0,))
      assert not runtime.directory.entries("service") or all(
        entry.name != "store" for entry in runtime.directory.entries("service")
      )
      message = {
        "id": "10",
        "channel_id": "55",
        "guild_id": "7",
        "content": "!ping",
        "author": {
          "id": "2",
          "username": "ada",
          "discriminator": "0",
          "avatar": None,
          "global_name": None,
        },
        "timestamp": "2026-01-01T00:00:00+00:00",
        "edited_timestamp": None,
        "tts": False,
        "mention_everyone": False,
        "mentions": [],
        "mention_roles": [],
        "attachments": [],
        "embeds": [],
        "pinned": False,
        "type": 0,
      }
      await SESSIONS[0].dispatch("MESSAGE_CREATE", message)
      await eventually(lambda: bool(sent))
      assert sent[0].url.path == "/channels/55/messages"
      assert json.loads(sent[0].content) == {"content": "pong"}

  asyncio.run(exercise())


def test_http_bridge_forwards_requests_and_probes(nats_url: str) -> None:
  from pydantic import BaseModel

  from micro.http import HTTPBridge

  class Name(BaseModel):
    name: str

  greet = RequestSchema[Name, Name](id="example.greet", input=Name, output=Name)
  service = Service("greeter")

  @service.handle(greet)
  async def handle(request: Name) -> Name:
    return Name(name=f"hi {request.name}")

  async def exercise() -> None:
    bridge = HTTPBridge(port=0)
    async with Runtime(nats_url) as runtime:
      await runtime.add(service, bridge)
      port = bridge._server.servers[0].sockets[0].getsockname()[1]  # pyright: ignore
      async with httpx2.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
        assert (await client.get("/health/ready")).status_code == 204
        reply = await client.post("/requests/example.greet", json={"name": "ada"})
        assert reply.json() == {"name": "hi ada"}
        invalid = await client.post("/requests/example.greet", json={"nope": 1})
        assert invalid.status_code == 422
        missing = await client.post("/requests/example.missing", json={})
        assert missing.status_code == 503
        components = (await client.get("/components")).json()
        assert {"greeter", "http"} <= {entry["name"] for entry in components}

  asyncio.run(exercise())


def test_supervisor_runs_scales_and_rolls_a_deployment(
  nats_url: str, tmp_path: Path
) -> None:
  (tmp_path / "app.py").write_text(
    textwrap.dedent(
      """
      from micro.service import RequestSchema, Service

      PING = RequestSchema[str, str](id="deploy.ping", input=str, output=str)
      service = Service("pinger")

      @service.handle(PING)
      async def ping(value: str) -> str:
        return value
      """
    )
  )
  (tmp_path / "micro.toml").write_text(
    textwrap.dedent(
      f"""
      name = "test"
      nats = "{nats_url}"

      [processes.pinger]
      components = ["app:service"]
      replicas = 1
      """
    )
  )

  async def exercise() -> None:
    env = os.environ | {"MICRO_LOG_LEVEL": "WARNING"}
    up = await asyncio.create_subprocess_exec(
      sys.executable, "-m", "micro", "up", "micro.toml", cwd=tmp_path, env=env
    )

    async def control(*args: str) -> dict[str, Any]:
      process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "micro",
        *args,
        cwd=tmp_path,
        env=env,
        stdout=asyncio.subprocess.PIPE,
      )
      out, _ = await process.communicate()
      return json.loads(out)

    try:
      async with Runtime(nats_url) as runtime:

        def pingers() -> int:
          return sum(e.name == "pinger" for e in runtime.directory.entries("service"))

        await eventually(lambda: pingers() == 1, timeout=30)
        assert (await control("scale", "pinger", "3"))["ok"]
        await eventually(lambda: pingers() == 3, timeout=30)
        before = {p["pid"] for p in (await control("ps"))["processes"]}
        rolled = await control("roll", "pinger")
        assert rolled["ok"]
        after = {p["pid"] for p in rolled["processes"]}
        assert len(after) == 3 and not before & after
        reply = await runtime.nats.request(
          subjects.request("deploy.ping"), b'"x"', timeout=5
        )
        assert reply.data == b'"x"'
        assert (await control("scale", "pinger", "1"))["ok"]
        await eventually(lambda: pingers() == 1, timeout=30)
    finally:
      up.send_signal(signal.SIGTERM)
      assert await asyncio.wait_for(up.wait(), 60) == 0

  asyncio.run(exercise())
