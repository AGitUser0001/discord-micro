"""End-to-end smoke test: the whole Micro stack against scripts/fake_discord.py.

    uv run python scripts/smoke.py            # everything
    uv run python scripts/smoke.py sync       # only scenarios whose name contains "sync"

Boots a real nats-server, the real Gateway worker (hikari's own websocket
client), HTTP worker, interaction router, command sync, and a small service,
then drives them the way Discord would. Exit status is the number of failures.
"""

import asyncio
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any, Self

sys.path.insert(0, str(Path(__file__).parent))

import hikari
from fake_discord import FakeDiscord
from nats.js.api import StorageType
from pydantic import BaseModel, JsonValue

from micro import subjects
from micro.discord import DiscordHTTPClient, DiscordHTTPWorker
from micro.discord.filters import all_of, content_startswith, ignore_bots
from micro.discord.interactions import (
  Commands,
  CommandSync,
  Components,
  CustomId,
  Interaction,
  InteractionRouter,
  Modals,
  Route,
  RuntimeCommands,
  option,
)
from micro.discord.messages import reply_to
from micro.discord.ui import Button, Modal, TextInput
from micro.gateway import GatewayWorker
from micro.runtime import Runtime
from micro.schemas import events
from micro.service import Service

TOKEN = (
  "MTAw.Gabcde." + "x" * 27
)  # the first segment is base64("100"), the application ID
ROOT = Path(__file__).resolve().parent.parent


class Wave(BaseModel):
  name: str


WAVE = CustomId("smoke.wave", Wave)
FEEDBACK = CustomId("smoke.feedback")


class App:
  """A small service covering the main interaction shapes."""

  def __init__(self, *, guild_commands: tuple[int, ...] = ()) -> None:
    self.feedback: list[str] = []
    self.service = service = Service("smoke")
    commands = Commands(service)
    components = Components(service)
    modals = Modals(service)

    @service.listen(
      events.MESSAGE_CREATE, when=all_of(ignore_bots, content_startswith("!ping"))
    )
    async def ping(message: object) -> None:
      await reply_to(DiscordHTTPClient(service.runtime), message, "pong")

    @commands.slash("hello", description="Say hello")
    async def hello(ctx: Interaction, name: str = "world") -> None:
      await ctx.respond(
        f"Hello, {name}!",
        components=[Button("Wave back", custom_id=WAVE.encode(Wave(name=name)))],
      )

    @components.match(WAVE)
    async def wave(ctx: Interaction, state: Wave) -> None:
      await ctx.respond(
        f"{ctx.user.display_name} waves at {state.name}.", ephemeral=True
      )

    @commands.slash("feedback", description="Open a modal")
    async def ask(ctx: Interaction) -> None:
      await ctx.modal(
        Modal(
          FEEDBACK.encode(),
          "Feedback",
          [TextInput("text", "Thoughts", style="paragraph")],
        )
      )

    @modals.match(FEEDBACK)
    async def got(ctx: Interaction) -> None:
      self.feedback.append(ctx.fields["text"])
      await ctx.respond("Thanks!", ephemeral=True)

    @commands.slash("slow", description="Defer, then answer")
    async def slow(ctx: Interaction) -> None:
      await ctx.defer()
      await asyncio.sleep(0.2)
      await ctx.respond("done")

    self.dynamic = RuntimeCommands(service)

    @self.dynamic.handler
    async def custom(ctx: Interaction) -> None:
      await ctx.respond(f"{ctx.command_name}@{ctx.guild_id} {ctx.option_values}")

    if guild_commands:
      guilded = Commands(service, guild_ids=guild_commands)

      @guilded.slash("guilded", description="Only in some guilds")
      async def only(ctx: Interaction) -> None:
        await ctx.respond("guilded")


def free_port() -> int:
  with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    return sock.getsockname()[1]


async def wait_listening(port: int) -> None:
  """Return as soon as something accepts connections on the port."""
  while True:
    try:
      _, writer = await asyncio.open_connection("127.0.0.1", port)
    except OSError:
      await asyncio.sleep(0.02)
      continue
    writer.close()
    return


class Stack:
  """NATS, the fake Discord, and every Micro component, wired together."""

  def __init__(
    self,
    app: App,
    *,
    guilds: tuple[str, ...] = ("500",),
    intents: hikari.Intents | None = None,
    seed_intents: bool = True,
    first: Sequence[Any] = (),
    router: InteractionRouter | None = None,
    gateway: dict[str, Any] | None = None,
    extra_gateways: int = 0,
    members: dict[str, list[dict[str, Any]]] | None = None,
  ) -> None:
    self.members = members or {}
    self.app = app
    self.first = tuple(first)
    self.router = router
    self.gateway = gateway or {}
    self.extra_gateways = extra_gateways
    self.intents = intents
    self.seed_intents = seed_intents
    self.guilds = guilds
    self.connection_events: list[dict[str, Any]] = []

  async def __aenter__(self) -> Self:
    self.fake = FakeDiscord(TOKEN, guilds=self.guilds)
    self.fake.members = self.members
    api = await self.fake.start()
    self._dir = tempfile.TemporaryDirectory()
    port = free_port()
    binary = shutil.which("nats-server") or str(ROOT / ".venv/bin/nats-server")
    self._nats = await asyncio.create_subprocess_exec(
      binary,
      "-js",
      "-p",
      str(port),
      "-sd",
      self._dir.name,
      stdout=asyncio.subprocess.DEVNULL,
      stderr=asyncio.subprocess.DEVNULL,
    )
    await wait_listening(port)
    self.runtime = Runtime(
      f"nats://127.0.0.1:{port}", name="smoke", storage=StorageType.MEMORY
    )
    await self.runtime.__aenter__()

    async def note(message: Any) -> None:
      self.connection_events.append(json.loads(message.data))

    await self.runtime.nats.subscribe("micro.gateway.connection.>", cb=note)
    intents = self.intents or (
      hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT
    )
    self.sync = CommandSync()
    if self.seed_intents:
      from micro.gateway import GatewayControl

      await GatewayControl(self.runtime).set_intents(int(intents))
    await self.runtime.add(
      *self.first,
      DiscordHTTPWorker(TOKEN, api_url=api),
      GatewayWorker(TOKEN, api_url=api, **self.gateway),
      *(
        GatewayWorker(
          TOKEN,
          api_url=api,
          name=f"gateway{i}",
          **self.gateway,
        )
        for i in range(self.extra_gateways)
      ),
      self.router or InteractionRouter(),
      self.sync,
      self.app.service,
    )
    return self

  async def __aexit__(self, *error: object) -> None:
    try:
      await self.runtime.__aexit__(*error)  # type: ignore[arg-type]
    except Exception as exc:  # shutdown noise must not hide a result
      print(f"  (shutdown: {type(exc).__name__}: {exc})")
    self._nats.terminate()
    await self._nats.wait()
    await self.fake.stop()
    self._dir.cleanup()

  # Helpers ---------------------------------------------------------------------

  def names(self, scope: str = "global") -> list[str]:
    return sorted(c["name"] for c in self.fake.commands.get(scope, []))

  async def interact(
    self, payload: dict[str, Any], count: int = 1, timeout: float = 8.0
  ) -> list[Any]:
    """Send an interaction; return the fake Discord's calls for it once `count` arrived."""
    token = payload["token"]

    def mine() -> list[Any]:
      return [c for c in self.fake.calls if token in c.path]

    await self.fake.send(payload)
    await self.fake.until(lambda: len(mine()) >= count, timeout)
    await asyncio.sleep(0.1)
    return mine()


results: list[tuple[str, bool]] = []


def check(name: str, ok: bool, detail: object = "") -> None:
  results.append((name, ok))
  print(
    f"  {'PASS' if ok else 'FAIL'}  {name}"
    + (f"   [{detail}]" if detail and not ok else "")
  )


def reply_of(calls: list[Any]) -> tuple[int | None, dict[str, Any]]:
  for call in calls:
    if call.path.endswith("/callback") and call.status == 204:
      return call.body["type"], call.body.get("data") or {}
  return None, {}


# Scenarios ---------------------------------------------------------------------


async def basics() -> None:
  print("basics: gateway, interactions, events")
  app = App()
  async with Stack(app) as s:
    f = s.fake
    check(
      "gateway identified once",
      await f.until(lambda: f.identifies == 1, 15),
      f.identifies,
    )
    check(
      "connection READY published on NATS",
      await f.until(
        lambda: any(e.get("kind") == "ready" for e in s.connection_events), 5
      ),
      s.connection_events,
    )
    check(
      "commands registered with Discord",
      await f.until(lambda: s.names() == ["feedback", "hello", "slow"], 10),
      s.names(),
    )

    calls = await s.interact(
      f.slash("hello", [{"name": "name", "type": 3, "value": "bob"}])
    )
    kind, data = reply_of(calls)
    check(
      "slash command answered with a message",
      kind == 4 and "Hello, bob" in data.get("content", ""),
      calls,
    )
    buttons = [
      c for row in data.get("components", []) for c in row.get("components", [])
    ]
    check(
      "reply carries a typed button",
      bool(buttons) and buttons[0]["custom_id"].startswith("smoke.wave:"),
      buttons,
    )

    if buttons:
      calls = await s.interact(f.component(buttons[0]["custom_id"]))
      kind, data = reply_of(calls)
      check(
        "button click decoded its state",
        kind == 4 and "waves at bob" in data.get("content", ""),
        calls,
      )

    calls = await s.interact(f.slash("feedback"))
    kind, data = reply_of(calls)
    check("slash command opened a modal", kind == 9, calls)
    if kind == 9:
      calls = await s.interact(f.modal_submit(data["custom_id"], {"text": "lovely"}))
      check(
        "modal submit reached its handler", app.feedback == ["lovely"], app.feedback
      )

    calls = await s.interact(f.slash("slow"), count=3)
    types = [c.body.get("type") for c in calls if c.path.endswith("/callback")]
    edits = [c for c in calls if c.method == "PATCH"]
    check(
      "defer then respond: type 5 callback, then the original is edited",
      types == [5] and len(edits) == 1,
      [(c.method, c.status) for c in calls],
    )

    calls = await s.interact(f.component("nobody.handles:1"))
    kind, data = reply_of(calls)
    check(
      "unhandled component gets an ephemeral 'unavailable' reply",
      kind == 4 and "isn't available" in data.get("content", ""),
      calls,
    )

    await f.dispatch("MESSAGE_CREATE", f.message_create("!ping"))
    check(
      "!ping handled from a normal MESSAGE_CREATE (flags 0)",
      await f.until(lambda: len(f.where("POST", r"/channels/600/messages")) == 1, 8),
    )

    pongs = len(f.where("POST", r"/channels/600/messages"))
    await f.drop_gateway()
    check(
      "gateway resumed after a dropped connection",
      await f.until(lambda: f.resumes == 1, 15),
      (f.identifies, f.resumes),
    )
    check("resume kept the session (no new identify)", f.identifies == 1, f.identifies)
    await f.dispatch("MESSAGE_CREATE", f.message_create("!ping"))
    await f.until(lambda: len(f.where("POST", r"/channels/600/messages")) > pongs, 8)
    await asyncio.sleep(0.5)
    check(
      "events flow after resume, exactly once",
      len(f.where("POST", r"/channels/600/messages")) == pongs + 1,
      len(f.where("POST", r"/channels/600/messages")) - pongs,
    )

    f.rate_limit(r"/interactions/.+/callback", retry_after=0.3, times=1)
    started = time.monotonic()
    calls = await s.interact(f.slash("hello"), count=2)
    statuses = [c.status for c in calls if c.path.endswith("/callback")]
    check(
      "429 on a callback is retried and then succeeds", statuses == [429, 204], statuses
    )
    check("the retry waited out Retry-After", time.monotonic() - started >= 0.3)


async def runtime_command_scenarios() -> None:
  print("runtime commands: created, served, and removed while running")
  app = App()
  async with Stack(app, guilds=("500", "600")) as s:
    f = s.fake
    base = ["feedback", "hello", "slow"]
    await f.until(lambda: s.names() == base, 10)
    await app.dynamic.add("greet", "Custom", options=[option("who")], guild_id=500)
    check(
      "a runtime command is registered in its guild only",
      await f.until(lambda: s.names("500") == ["greet"], 10) and s.names() == base,
      (s.names("500"), s.names()),
    )
    await asyncio.sleep(0.5)
    calls = await s.interact(
      f.slash("greet", [{"name": "who", "type": 3, "value": "bo"}])
    )
    kind, data = reply_of(calls)
    check(
      "it runs the shared handler with name, guild and options",
      kind == 4
      and "greet@" in data.get("content", "")
      and "'who': 'bo'" in data["content"],
      data,
    )
    await app.dynamic.add("greet", "Changed", guild_id=600)
    check(
      "the same name in another guild is one command in two scopes",
      await f.until(lambda: s.names("600") == ["greet"], 10)
      and s.names("500") == ["greet"],
      (s.names("500"), s.names("600")),
    )
    await app.dynamic.add("wide", "Everywhere")
    check(
      "no guild means global, next to the declared commands",
      await f.until(lambda: s.names() == sorted([*base, "wide"]), 10),
      s.names(),
    )
    await app.dynamic.add("hello", "Clash", guild_id=500)
    await asyncio.sleep(1)
    check(
      "a name declared in code is not overridden",
      s.names("500") == ["greet"],
      s.names("500"),
    )
    await app.dynamic.remove("hello", guild_id=500)
    check(
      "removing from one guild keeps the others",
      await app.dynamic.remove("greet", guild_id=500)
      and await f.until(lambda: s.names("500") == [], 10)
      and s.names("600") == ["greet"],
      (s.names("500"), s.names("600")),
    )
    check(
      "removing the last scope forgets the command",
      await app.dynamic.remove("greet", guild_id=600)
      and not await app.dynamic.remove("greet", guild_id=600)
      and await f.until(lambda: s.names("600") == [], 10),
      s.names("600"),
    )
    check(
      "commands() lists what is left",
      sorted(await app.dynamic.commands()) == ["1:wide"],
      await app.dynamic.commands(),
    )


async def member_cache_scenarios() -> None:
  print("member cache: every member, from every shard, without REST")
  from micro.discord.state import DiscordState
  from micro.gateway.projection import GatewayProjection
  from micro.store import Store
  from micro.store.sqlite import SQLiteGraph

  def member(user_id: str, name: str, roles: list[str]) -> dict[str, Any]:
    return {
      "user": {"id": user_id, "username": name, "discriminator": "0", "avatar": None},
      "roles": roles,
      "joined_at": "2024-01-01T00:00:00+00:00",
      "deaf": False,
      "mute": False,
      "flags": 0,
    }

  intents = (
    hikari.Intents.ALL_UNPRIVILEGED
    | hikari.Intents.MESSAGE_CONTENT
    | hikari.Intents.GUILD_MEMBERS
  )
  cache_dir = tempfile.TemporaryDirectory()
  fake_members = {
    "500": [member("1", "ann", ["10"]), member("2", "bob", ["11"])],
    "600": [member("1", "ann", ["20"])],
  }
  async with Stack(
    App(),
    guilds=("500", "600"),
    intents=intents,
    first=[
      Store(SQLiteGraph(os.path.join(cache_dir.name, "cache.db"))),
      GatewayProjection(),
    ],
    members=fake_members,
  ) as s:
    f = s.fake
    await f.until(lambda: len(f.member_requests) >= 2, 15)
    state = DiscordState(s.runtime)

    async def cached() -> bool:
      try:
        return await state._projected(600, "member", "600:1") is not None
      except Exception:
        return False

    for _ in range(40):
      if await cached():
        break
      await asyncio.sleep(0.5)
    rest = len(f.where("GET", r"/members/"))
    ann_500 = await state.member(500, 1)
    ann_600 = await state.member(600, 1)
    bob = await state.member(500, 2)
    check(
      "every guild is asked for all its members once per connection",
      sorted(r["guild_id"] for r in f.member_requests) == ["500", "600"]
      and all(r["query"] == "" and r["limit"] == 0 for r in f.member_requests),
      (f.member_requests, f.identifies, [e.get("kind") for e in s.connection_events]),
    )
    check(
      "members are answered from the cache, not REST",
      {ann_500.source, ann_600.source, bob.source} == {"projection"}
      and len(f.where("GET", r"/members/")) == rest,
      (ann_500.source, ann_600.source, bob.source),
    )
    check(
      "one user keeps a different member record in each guild",
      ann_500.value.roles == ["10"] and ann_600.value.roles == ["20"],
      (ann_500.value.roles, ann_600.value.roles),
    )
    await f.dispatch(
      "GUILD_MEMBER_UPDATE", {"guild_id": "500", **member("2", "bob", ["11", "12"])}
    )
    await f.dispatch("GUILD_MEMBER_ADD", {"guild_id": "600", **member("3", "cy", [])})
    await asyncio.sleep(1.5)
    check(
      "member updates and joins reach the cache",
      (await state.member(500, 2)).value.roles == ["11", "12"]
      and (await state.member(600, 3)).source == "projection",
    )
    await f.dispatch(
      "GUILD_MEMBER_REMOVE", {"guild_id": "500", "user": member("2", "bob", [])["user"]}
    )
    await asyncio.sleep(1.5)
    check(
      "a member who left leaves the cache",
      (await state._projected(500, "member", "500:2")) is None
      and (await state._projected(600, "member", "600:1")) is not None,
    )
  cache_dir.cleanup()


async def custom_package_scenarios() -> None:
  print("custom package: members make commands, text lives in the store")
  import importlib.util
  from types import SimpleNamespace

  from micro.store import Store
  from micro.store.sqlite import SQLiteGraph

  spec = importlib.util.spec_from_file_location(
    "custom_pkg", ROOT / "packages/custom/__init__.py"
  )
  assert spec and spec.loader
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as raw:
    async with Stack(
      SimpleNamespace(service=module.service),  # type: ignore[arg-type]
      first=[Store(SQLiteGraph(os.path.join(raw, "custom.db")))],
    ) as s:
      f = s.fake
      await f.until(lambda: s.names() == ["custom"], 15)

      async def say(name: str, options: list[dict[str, Any]] | None = None) -> str:
        calls = await s.interact(f.slash(name, options))
        return reply_of(calls)[1].get("content", "")

      def custom(sub: str, **values: str) -> list[dict[str, Any]]:
        return [
          {
            "name": sub,
            "type": 1,
            "options": [{"name": k, "type": 3, "value": v} for k, v in values.items()],
          }
        ]

      check(
        "/custom add makes a command",
        "Made /hello" in await say("custom", custom("add", name="hello", text="Hi!")),
      )
      check(
        "it is registered in the guild",
        await f.until(lambda: s.names("500") == ["hello"], 15),
        s.names("500"),
      )
      await asyncio.sleep(0.5)
      check("the new command answers with its text", await say("hello") == "Hi!")
      await say("custom", custom("add", name="hello", text="Hello again"))
      await asyncio.sleep(0.3)
      check("adding it again changes the text", await say("hello") == "Hello again")
      check("/custom list shows it", "/hello" in await say("custom", custom("list")))
      check(
        "/custom remove deletes it",
        "Removed" in await say("custom", custom("remove", name="hello"))
        and await f.until(lambda: s.names("500") == [], 15),
        s.names("500"),
      )


async def endpoint_scenarios() -> None:
  print("http endpoint: signed interactions answered in the HTTP reply")
  import httpx2
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
  from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

  from micro._ed25519 import verify as verify_fast
  from micro._ed25519 import verify_python as verify
  from micro.discord.interactions import InteractionEndpoint

  # RFC 8032 test vector 2 (one-byte message), then random keys against the C library.
  vector_key = bytes.fromhex(
    "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"
  )
  vector_sig = bytes.fromhex(
    "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
    "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
  )
  agrees = verify(vector_key, b"\x72", vector_sig) and not verify(
    vector_key, b"\x73", vector_sig
  )
  for index in range(20):
    key = Ed25519PrivateKey.generate()
    raw = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    message = os.urandom(index * 7)
    signature = key.sign(message)
    broken = bytes([signature[0] ^ 1]) + signature[1:]
    agrees = (
      agrees and verify(raw, message, signature) and not verify(raw, message, broken)
    )
    agrees = agrees and not verify(raw, message + b"x", signature)
  agrees = agrees and not verify(vector_key, b"\x72", vector_sig[:-1])
  agrees = agrees and verify_fast(vector_key, b"\x72", vector_sig)
  agrees = agrees and not verify_fast(vector_key, b"\x73", vector_sig)
  check("pure-Python Ed25519 agrees with RFC 8032 and the C library", agrees)

  private = Ed25519PrivateKey.generate()
  public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
  port = free_port()
  async with Stack(App()) as s:
    f = s.fake
    await s.runtime.add(InteractionEndpoint(public_key=public, port=port))
    await f.until(lambda: s.names() == ["feedback", "hello", "slow"], 10)
    url = f"http://127.0.0.1:{port}/interactions"

    async def post(payload: dict[str, Any], *, sign: bool = True) -> httpx2.Response:
      body = json.dumps(payload).encode()
      stamp = "1700000000"
      signature = private.sign(stamp.encode() + body).hex() if sign else "00" * 64
      async with httpx2.AsyncClient() as client:
        return await client.post(
          url,
          content=body,
          headers={"x-signature-ed25519": signature, "x-signature-timestamp": stamp},
          timeout=15,
        )

    check(
      "a bad signature is refused",
      (await post({"type": 1}, sign=False)).status_code == 401,
    )
    pong = await post({"type": 1})
    check(
      "PING is answered with PONG",
      pong.status_code == 200 and pong.json() == {"type": 1},
      pong.text,
    )

    callbacks = len(f.where("POST", r"/callback$"))
    reply = await post(f.slash("hello", [{"name": "name", "type": 3, "value": "bo"}]))
    body = reply.json()
    check(
      "the handler's first response is the HTTP reply",
      reply.status_code == 200
      and body["type"] == 4
      and "Hello, bo" in body["data"]["content"],
      reply.text,
    )
    check(
      "no callback request was needed",
      len(f.where("POST", r"/callback$")) == callbacks,
    )
    modal = await post(f.slash("feedback"))
    check("a modal is returned the same way", modal.json()["type"] == 9, modal.text)
    unknown = await post(f.component("nobody.handles:1"))
    check(
      "an interaction nobody handles is answered too",
      "isn't available" in unknown.json()["data"]["content"],
      unknown.text,
    )
    slow_payload = f.slash("slow")
    reply = await post(slow_payload)
    f.acknowledge(slow_payload)
    await f.until(lambda: len(f.where("PATCH", r"/messages/@original")) == 1, 8)
    check(
      "a deferral is the reply and the final answer edits the original",
      reply.json()["type"] == 5 and len(f.where("PATCH", r"/messages/@original")) == 1,
      reply.text,
    )


async def docs_scenarios() -> None:
  print("docs: every page renders, every export is documented")
  from micro import _docs, _docs_api

  try:
    pages = _docs.render(strict=True)
    problems: list[str] = []
  except _docs.DocsError as error:
    pages, problems = {}, error.problems
  check("every page renders with no broken reference", not problems, problems[:5])
  check("the docs have pages", len(pages) > 20, len(pages))
  missing = _docs_api.missing_entries()
  check("every public name has a reference entry", not missing, missing[:10])
  bare = _docs_api.missing_descriptions()
  check("every documented object has a description", not bare, bare[:10])


async def ui_hooks_scenarios() -> None:
  print("ui hooks: middleware around building and serializing components")
  from micro.discord.ui import (
    ActionRow,
    Button,
    Container,
    Label,
    Modal,
    StringSelect,
    TextInput,
    hooks,
  )

  with hooks.scoped():
    order: list[str] = []

    @hooks.build(only=Button)
    def secondary(call: Any, next: Any) -> Any:
      order.append("build")
      call.kwargs.setdefault("style", "secondary")
      return next()

    @hooks.serialize
    def outer(component: Any, next: Any) -> Any:
      order.append("outer")
      data = next()
      if "custom_id" in data:
        data["custom_id"] = "o." + data["custom_id"]
      return data

    @hooks.serialize
    def inner(component: Any, next: Any) -> Any:
      data = next()
      if "custom_id" in data:
        data["custom_id"] += ".i"
      return data

    button = Button("Go", custom_id="go")
    check(
      "build middleware changes the arguments",
      button.style == "secondary" and order == ["build"],
      button,
    )
    check(
      "serialize middleware nests, first added outermost",
      button.to_dict()["custom_id"] == "o.go.i",
      button.to_dict(),
    )
    tree: Any = Container(
      ActionRow(Button("x", custom_id="x"), StringSelect("pick", ["a"]))
    ).to_dict()
    ids = [c["custom_id"] for row in tree["components"] for c in row["components"]]
    check("nested components are intercepted too", ids == ["o.x.i", "o.pick.i"], ids)
    modal = Modal("form", "T", [Label("L", TextInput("t"))]).to_dict()
    check(
      "a modal and its inputs are intercepted",
      modal["custom_id"] == "o.form.i" and "o.t.i" in str(modal),
      modal,
    )

    @hooks.build(only=Button)
    def replace(call: Any, next: Any) -> Any:
      return Button("replaced", custom_id="r")

    check(
      "build middleware can return a different component",
      Button("a", custom_id="b").label == "replaced",
    )
    hooks.remove(replace)
    hooks.remove(outer)
    check(
      "remove() unregisters middleware",
      Button("a", custom_id="b").to_dict()["custom_id"] == "b.i",
    )
    check(
      "only= limits which components it sees",
      StringSelect("p", ["a"]).to_dict()["custom_id"] == "p.i",
    )
  check(
    "scoped() restores the registered middleware",
    not hooks.active and Button("a", custom_id="b").to_dict()["custom_id"] == "b",
  )


async def ui_limits_scenarios() -> None:
  print(
    "ui limits: counts accumulate as components are built; limits are checked on serialize"
  )
  from micro.discord import ui
  from micro.discord.ui import (
    ActionRow,
    Button,
    Container,
    Label,
    MediaGallery,
    MediaItem,
    Section,
    TextDisplay,
    TextInput,
    Thumbnail,
  )

  def button(i: int) -> Button:
    return Button(f"b{i}", custom_id=f"b{i}")

  def box() -> Container:  # container + text + row + 4 buttons = 7
    return Container(TextDisplay("t"), ActionRow(*[button(j) for j in range(4)]))

  def refused(action: Any) -> str:
    try:
      action()
    except ValueError as error:
      return str(error)
    return ""

  check(
    "counts accumulate up the tree as it is built",
    box().components_count == 7 and box().text_count == 1,
  )
  section = Section("a", "bb", "ccc", accessory=Thumbnail("https://x/y.png"))
  check(
    "a section counts its texts and accessory, and their text",
    section.components_count == 5 and section.text_count == 6,
  )
  check(
    "text is counted in UTF-16 units: an emoji is 2",
    ui.utf16_length("a😀") == 3 and TextDisplay("😀" * 2001).count == 4002,
  )
  check(
    "so 2001 emoji overflow a 4000-unit Text Display",
    "content is 4002" in refused(lambda: TextDisplay("😀" * 2001).to_dict()),
  )
  check(
    "a container sums its children's counts",
    Container(box(), section).components_count == 13,
  )
  row = ActionRow(button(1), button(2), button(3))
  select_row = ActionRow(ui.StringSelect("pick", ["a", "b"]))
  check(
    "a row reads count, max and remaining",
    (row.count, row.max, row.remaining) == (3, 5, 2),
  )
  check(
    "a select takes the whole row: slots 5",
    ui.StringSelect.slots == 5 and ui.UserSelect.slots == 5 and Button.slots == 1,
  )
  check(
    "so a row with a select is full", (select_row.count, select_row.remaining) == (5, 0)
  )
  check(
    "and a select plus a button is 6 of 5",
    "slots is 6"
    in refused(lambda: ActionRow(ui.StringSelect("p", ["a"]), button(1)).to_dict()),
  )
  check(
    "max is readable on the class",
    (ActionRow.max, Section.max, ui.MediaGallery.max, TextDisplay.max, Container.max)
    == (5, 3, 10, 4000, 40),
  )
  check("a component with no main dimension has max None", ui.Separator.max is None)
  check(
    "every component has a count and a limit",
    all(isinstance(m, ui.Measure) for m in ActionRow(button(1)).measures)
    and {m.name: m.limit for m in ActionRow(button(1)).measures}["slots"] == 5,
  )
  check(
    "limits come from Discord's models",
    {m.name: m.limit for m in TextDisplay("x").measures}["content"] == 4000,
  )

  error = refused(lambda: ActionRow(*[button(i) for i in range(6)]).to_dict())
  check(
    "six buttons in a row fail when serialized, naming the count and limit",
    "slots is 6" in error and "allows 5" in error,
    error,
  )
  check(
    "building it does not fail: validation is serialization middleware",
    ActionRow(*[button(i) for i in range(6)]).components_count == 7,
  )
  check(
    "a gallery of eleven fails",
    "items is 11"
    in refused(
      lambda: MediaGallery(
        *[MediaItem(f"https://x/{i}.png") for i in range(11)]
      ).to_dict()
    ),
  )
  check(
    "text over 4000 in one display fails",
    "content is 4001" in refused(lambda: TextDisplay("x" * 4001).to_dict()),
  )
  check(
    "a label over 45 characters fails",
    "label is 46" in refused(lambda: Label("x" * 46, TextInput("t")).to_dict()),
  )
  check(
    "a text input value over 4000 fails",
    "value is 4001" in refused(lambda: TextInput("t", value="x" * 4001).to_dict()),
  )
  check(
    "a container over 40 in all fails on its own",
    "components in all is 42"
    in refused(lambda: Container(*[TextDisplay("t") for _ in range(41)]).to_dict()),
  )

  check(
    "five containers (35) are fine",
    bool(ui.message_body(components=[box() for _ in range(5)])),
  )
  check(
    "eight (56), each fine alone, fail as a message",
    "components in all is 56"
    in refused(lambda: ui.message_body(components=[box() for _ in range(8)])),
  )
  texts = [TextDisplay("x" * 1500) for _ in range(3)]
  check(
    "text adds up across the message (4500 > 4000)",
    "text in all is 4500" in refused(lambda: ui.message_body(components=texts)),
  )
  check(
    "validate() applies the same totals",
    bool(refused(lambda: ui.validate([box() for _ in range(8)]))),
  )
  with ui.hooks.scoped():
    ui.hooks.remove(ui.check_limits)
    check(
      "the check is middleware: remove it and it is off",
      ActionRow(*[button(i) for i in range(6)]).to_dict()["type"] == 1,
    )


async def colour_scenarios() -> None:
  print("colour: a helper, and colour spelled the Canadian way")
  from micro.discord import ui
  from micro.discord.colour import Colour
  from micro.discord.objects import Role, User

  check(
    "a colour is an int in range",
    Colour(0x5865F2) == 0x5865F2 and isinstance(Colour.BLURPLE, int),
  )
  check(
    "it parses numbers, hex, short hex, names and tuples to the same colour",
    Colour.parse(0x5865F2)
    == Colour.parse("#5865f2")
    == Colour.parse("blurple")
    == Colour.parse((88, 101, 242))
    == Colour.from_hex("5865F2"),
  )
  check("short hex doubles each digit", Colour.from_hex("#58f") == 0x5588FF)
  check(
    "rgb, hex and parts read back",
    (Colour.BLURPLE.rgb, Colour.BLURPLE.hex, Colour.BLURPLE.r)
    == ((88, 101, 242), "#5865f2", 88),
  )
  check(
    "lighten, darken and mix make new colours",
    Colour.BLURPLE.lighten(0.2).hex == "#7984f5"
    and Colour.BLURPLE.darken(0.2).hex == "#4651c2"
    and Colour.RED.mix("blue").hex == "#906d90",
  )
  for bad in (0x1000000, -1, "nope", (1, 2, 300)):
    try:
      Colour.parse(bad)  # type: ignore[arg-type]
      refused = False
    except ValueError:
      refused = True
    check(f"{bad!r} is refused", refused)
  check(
    "embed and container take any colour-like and send Discord's key as a plain int",
    ui.embed("t", colour="teal")["color"] == 0x1ABC9C
    and type(ui.embed("t", colour=Colour.GREEN)["color"]) is int
    and ui.Container(ui.TextDisplay("x"), accent_colour=(1, 2, 3)).to_dict()[
      "accent_color"
    ]
    == 0x010203,
  )
  role = Role.model_validate({"id": "1", "color": 0x5865F2})
  check(
    "a role's colour is a Colour read from Discord's color",
    isinstance(role.colour, Colour) and role.colour == 0x5865F2,
  )
  check(
    "and it dumps back to color on the wire",
    role.model_dump(by_alias=True)["color"] == 0x5865F2
    and Role(id="2", colour=Colour(0xFF0000)).colour == 0xFF0000,
  )
  check(
    "a user's accent_colour is aliased the same way",
    User.model_validate({"id": "1", "accent_color": 5}).accent_colour == 5
    and User(id="1").accent_colour is None,
  )


async def signed_ids_scenarios() -> None:
  print("signed custom ids: the middleware example from the docs, as written")
  import re

  from micro import _docs

  source = (_docs._source() / "middleware.rst").read_text()  # pyright: ignore[reportPrivateUsage]
  blocks = re.findall(
    r"\.\. code-block:: python\n\n   # (myapp/\w+\.py)[^\n]*\n((?:   .*\n|\n)+)", source
  )
  files = {
    name: "\n".join(line[3:] for line in body.splitlines()) for name, body in blocks
  }
  check(
    "the docs give the signing module and the router",
    set(files) >= {"myapp/signing.py", "myapp/router.py", "myapp/ids.py"},
    list(files),
  )
  os.environ["CUSTOM_ID_SECRET"] = "s3cret"
  import sys
  import types

  package = types.ModuleType("myapp")
  package.__path__ = []  # type: ignore[attr-defined]
  sys.modules["myapp"] = package
  for name in ("signing", "router", "ids"):
    module = types.ModuleType(f"myapp.{name}")
    module.__package__ = "myapp"
    sys.modules[f"myapp.{name}"] = module
    exec(  # noqa: S102
      compile(files[f"myapp/{name}.py"], f"myapp/{name}.py", "exec"), module.__dict__
    )
  from micro.discord.ui import hooks

  signing, built = sys.modules["myapp.signing"], sys.modules["myapp.router"]
  async with Stack(App(), router=built.router) as s:
    f = s.fake
    await f.until(lambda: s.names() == ["feedback", "hello", "slow"], 10)
    plain = WAVE.encode(Wave(name="bo"))
    calls = await s.interact(f.component(signing.sign(plain)))
    kind, data = reply_of(calls)
    check(
      "a signed id reaches its handler under the plain id",
      kind == 4 and "waves at bo" in data.get("content", ""),
      data,
    )
    calls = await s.interact(f.component(plain))
    kind, data = reply_of(calls)
    check(
      "an unsigned id is refused and never routed",
      "no longer valid" in data.get("content", ""),
      data,
    )
    forged = plain + "~" + "0" * 16
    calls = await s.interact(f.component(forged))
    check(
      "a forged signature is refused",
      "no longer valid" in reply_of(calls)[1].get("content", ""),
    )
    calls = await s.interact(f.slash("hello"))
    kind, data = reply_of(calls)
    check("commands pass through untouched", kind == 4)
    buttons = [
      c for row in data.get("components", []) for c in row.get("components", [])
    ]
    sent = buttons[0]["custom_id"] if buttons else ""
    check(
      "the serialize hook signed the button the service sent as a plain id",
      "~" in sent
      and signing.verify(sent) is not None
      and signing.verify(sent).startswith("smoke.wave:"),
      sent,
    )
    calls = await s.interact(f.component(sent))
    check(
      "clicking that signed button reaches the handler",
      "waves at" in reply_of(calls)[1].get("content", ""),
      reply_of(calls),
    )
  hooks.remove(sys.modules["myapp.ids"].sign_custom_ids)


async def config_scenarios() -> None:
  print("config: typed, shared, revision-safe settings with refresh middleware")
  from pydantic import BaseModel, ConfigDict

  from micro.config import (
    Config,
    ConfigConflict,
    ConfigRejected,
    Refresh,
  )

  class Limits(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    rate: int = 10
    name: str = "default"

  port = free_port()
  binary = shutil.which("nats-server") or str(ROOT / ".venv/bin/nats-server")
  url = f"nats://127.0.0.1:{port}"
  with tempfile.TemporaryDirectory() as store:

    async def serve() -> Any:
      proc = await asyncio.create_subprocess_exec(
        binary, "-js", "-p", str(port), "-sd", store,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
      )  # fmt: skip
      await wait_listening(port)
      return proc

    server = await serve()
    try:
      a = Runtime(url, name="a", reconnect_time_wait=0.2)
      b = Runtime(url, name="b", reconnect_time_wait=0.2)
      await a.start()
      await b.start()

      before = Config(a, "limits", Limits).value
      check(
        "bootstrap settings are readable before anything connects",
        before == Limits() and not Config(a, "x", Limits).loaded,
      )

      one, two = await asyncio.gather(
        a.config("limits", Limits, bootstrap=Limits(rate=1)),
        b.config("limits", Limits, bootstrap=Limits(rate=2)),
      )
      check(
        "racing first starts create one document, and both see it",
        one.value == two.value
        and one.revision == two.revision
        and one.value.rate in (1, 2),
        (one.value, two.value),
      )
      first = one.revision
      assert first is not None

      # Revision-safe writes
      stale = await one.read()
      written = await one.update(rate=20)
      await two.wait_for(written.revision, timeout=5)
      check(
        "an update reaches the other process's snapshot",
        two.value.rate == 20 and two.revision == written.revision,
      )
      try:
        await one.set(
          stale.value.model_copy(update={"rate": 99}), revision=stale.revision
        )
        conflicted = False
      except ConfigConflict:
        conflicted = True
      check(
        "a write at a stale revision is refused",
        conflicted and (await one.read()).value.rate == 20,
      )
      results = await asyncio.gather(
        *(
          one.update(lambda c: c.model_copy(update={"rate": c.rate + 1}))
          for _ in range(5)
        ),
        *(
          two.update(lambda c: c.model_copy(update={"rate": c.rate + 1}))
          for _ in range(5)
        ),
      )
      check(
        "concurrent updates never lose one",
        (await one.read()).value.rate == 30,
        (await one.read()).value.rate,
      )
      last = max(r.revision for r in results)
      await one.wait_for(last, timeout=5)
      await two.wait_for(last, timeout=5)
      check(
        "both snapshots converge on the last revision",
        one.value == two.value and one.revision == last,
      )
      same = await one.update(rate=30)
      check("an update that changes nothing writes nothing", same.revision == last)
      try:
        await one.update(rate="lots")  # type: ignore[arg-type]
        invalid_write = False
      except Exception:
        invalid_write = True
      check(
        "an invalid value is refused before it is written",
        invalid_write and (await one.read()).revision == last,
      )

      # Middleware: order, old/new, reject
      seen: list[Any] = []

      async def record(refresh: Refresh[Limits], next: Any) -> None:
        seen.append(
          (refresh.old.rate, refresh.new.rate, refresh.initial, refresh.attempt)
        )
        await next()

      async def guard(refresh: Refresh[Limits], next: Any) -> None:
        if refresh.new.rate < 0:
          raise refresh.reject("negative")
        await next()

      one.use(record)
      one.use(guard)
      issues: list[Any] = []
      one.on_error(issues.append)
      applied: list[Any] = []
      one.on_change(applied.append)
      ok = await two.update(rate=40)
      await one.wait_for(ok.revision, timeout=5)
      check(
        "middleware sees the old and the incoming configuration",
        seen == [(30, 40, False, 1)],
        seen,
      )
      check(
        "on_change fires after it applied",
        [(x.old.rate, x.new.rate) for x in applied] == [(30, 40)],
        applied,
      )
      bad = await two.update(rate=-1)
      try:
        await one.wait_for(bad.revision, timeout=5)
        waited = "applied"
      except ConfigRejected:
        waited = "rejected"
      check(
        "rejected change: snapshot kept, waiter told, error reported",
        waited == "rejected"
        and one.value.rate == 40
        and [i.kind for i in issues] == ["rejected"],
        (waited, issues),
      )
      good = await two.update(rate=50)
      await one.wait_for(good.revision, timeout=5)
      check("a later good revision applies after a rejected one", one.value.rate == 50)

      # Failure keeps the snapshot and retries
      fails = {"left": 2}

      async def flaky(refresh: Refresh[Limits], next: Any) -> None:
        if refresh.new.name == "flaky" and fails["left"] > 0:
          fails["left"] -= 1
          raise RuntimeError("downstream is down")
        await next()

      one.use(flaky)
      issues.clear()
      flaky_write = await two.update(name="flaky")
      await asyncio.sleep(0.3)
      check(
        "a failing refresh keeps the previous snapshot",
        one.value.name == "default"
        and one.revision != flaky_write.revision
        and any(i.kind == "failed" for i in issues),
      )
      await one.wait_for(flaky_write.revision, timeout=10)
      check(
        "it is retried until it works (idempotent side effects)",
        one.value.name == "flaky" and fails["left"] == 0,
        fails,
      )

      # Defer
      hold = {"on": True}

      async def gate(refresh: Refresh[Limits], next: Any) -> None:
        if refresh.new.rate == 77 and hold["on"]:
          raise refresh.defer()
        await next()

      one.use(gate)
      deferred = await two.update(rate=77)
      await asyncio.sleep(0.3)
      check("a deferred change is held back", one.value.rate != 77)
      hold["on"] = False
      one.retry()
      await one.wait_for(deferred.revision, timeout=5)
      check("retry() applies a deferred change", one.value.rate == 77)

      # Latest wins while deferred
      hold["on"] = True
      await two.update(rate=77, name="x")
      latest = await two.update(rate=78)
      await one.wait_for(latest.revision, timeout=5)
      check("a newer revision supersedes a deferred one", one.value.rate == 78)

      # Invalid stored value is reported, not fatal
      issues.clear()
      table = await a.table(subjects.CONFIG_BUCKET, dict)
      await table.put("limits", {"rate": "not a number"})
      await asyncio.sleep(0.3)
      check(
        "an invalid stored value is reported and the snapshot kept",
        any(i.kind == "invalid" for i in issues) and one.value.rate == 78,
        issues,
      )
      recovered = await two.set(Limits(rate=5))
      await one.wait_for(recovered.revision, timeout=5)
      check("the next valid revision recovers", one.value.rate == 5)

      # watch()
      got: list[int] = []

      async def collect() -> None:
        async for change in one.watch():
          got.append(change.new.rate)
          if len(got) == 2:
            return

      watcher = asyncio.create_task(collect())
      await asyncio.sleep(0.05)
      await two.update(rate=6)
      await two.update(rate=7)
      await asyncio.wait_for(watcher, 5)
      check("watch() yields applied changes in order", got == [6, 7], got)

      # Reconnect: the server goes away and comes back
      server.terminate()
      await server.wait()
      await asyncio.sleep(0.5)
      server = await serve()
      outage = None
      for _ in range(60):
        try:
          outage = await two.update(rate=8)
          break
        except Exception:
          await asyncio.sleep(0.25)
      assert outage is not None
      await one.wait_for(outage.revision, timeout=20)
      check(
        "after the server restarts, changes still arrive",
        one.value.rate == 8 and one.revision == outage.revision,
      )

      # Persistence across process restarts
      await b.close()
      c = Runtime(url, name="c")
      await c.start()
      again = await c.config("limits", Limits, bootstrap=Limits(rate=999))
      check(
        "the document persists and wins over a new process's bootstrap",
        again.value.rate == 8 and again.revision == outage.revision,
        again.value,
      )

      # micro configure: the editor's logic, driven by keys against the real table
      from micro._configure import Configure
      from micro.gateway import GatewaySettings

      await a.config("gateway", GatewaySettings)
      ctable = await a.table(subjects.CONFIG_BUCKET, dict)
      app = Configure(
        ctable, {"gateway": GatewaySettings, "limits": None}, title="test"
      )
      await app.load()
      check(
        "the editor lists every stored table",
        app.names == ["gateway", "limits"],
        app.names,
      )

      async def stored(name: str) -> dict[str, Any]:
        found = await ctable.get(name)
        assert found is not None
        return found.value

      async def press(*keys: str) -> None:
        for key in keys:
          await app.handle(key)

      async def typed(text: str) -> None:
        await press(*text)

      await press("down", "enter")  # open limits (a table with no known model)
      await press("enter")
      check(
        "a table's fields are shown and can be opened",
        app.focus == "fields" and [k for k, _ in app.rows()][:1] == ["rate"],
        app.rows(),
      )
      await press("enter")
      await typed("99")
      await press("enter")
      check(
        "editing a field saves it against the latest revision",
        (await stored("limits"))["rate"] == 99 and app.message[0] == "ok",
        app.message,
      )
      await press("a")
      await typed("pool=4")
      await press("enter")
      check(
        "a table with no model accepts new keys",
        (await stored("limits"))["pool"] == 4,
        app.message,
      )
      await press("esc", "up", "enter", "down", "enter")  # gateway, then its intents
      await typed("unprivileged,message_content")
      await press("enter")
      gateway_doc = await stored("gateway")
      check(
        "gateway settings are an ordinary table",
        gateway_doc["intents"] == "unprivileged,message_content",
        gateway_doc,
      )
      await press("down", "down", "enter")  # lease_ttl
      await typed("1")
      await press("enter")
      check(
        "a value the model refuses is shown and not written",
        app.message[0] == "error" and (await stored("gateway"))["lease_ttl"] == 10.0,
        app.message,
      )
      await press("up", "up", "up", "enter", "esc")
      check("escape cancels an edit", app.input is None)
      await ctable.put("limits", {"rate": 5, "pool": 4})
      follower = asyncio.create_task(app.follow())
      await asyncio.sleep(0.3)
      await ctable.put("limits", {"rate": 6, "pool": 4})
      await asyncio.sleep(0.5)
      follower.cancel()
      check(
        "a change made elsewhere shows up",
        app.docs["limits"].value == {"rate": 6, "pool": 4}
        and "elsewhere" in app.message[1],
        app.message,
      )
      check(
        "the frame fits the terminal",
        all(len(x) < 400 for x in app.render(80, 20)[0])
        and len(app.render(80, 20)[0]) == 20,
      )

      # Cleanup
      from micro.config import ConfigClosed

      ended: list[str] = []

      async def iterate() -> None:
        async for _ in again.watch():
          pass
        ended.append("watch")

      iterating = asyncio.create_task(iterate())
      waiting = asyncio.create_task(again.wait_for(10**12))
      await asyncio.sleep(0.05)
      await c.close()
      await a.close()
      await asyncio.wait_for(iterating, 5)
      try:
        await asyncio.wait_for(waiting, 5)
        closed = "returned"
      except ConfigClosed:
        closed = "ConfigClosed"
      check(
        "close() ends watch() and releases waiters",
        ended == ["watch"] and closed == "ConfigClosed",
        (ended, closed),
      )
      await asyncio.sleep(0.1)
      check(
        "close() leaves no config tasks running",
        not [
          t
          for t in asyncio.all_tasks()
          if "micro.config." in t.get_name() and not t.done()
        ],
      )
    finally:
      server.terminate()
      await server.wait()


async def gateway_config_scenarios() -> None:
  print("gateway intents and settings: one way to set intents")
  import hikari

  from micro.gateway import GatewayControl

  offline = GatewayWorker(TOKEN)
  check(
    "bootstrap settings are available before NATS connects",
    offline.settings is None
    and offline.max_concurrency == 1
    and offline.lease_ttl == 10.0,
  )
  unprivileged = hikari.Intents.ALL_UNPRIVILEGED
  async with Stack(App(), seed_intents=False) as s:
    f = s.fake
    await f.until(lambda: f.identifies >= 1, 15)
    check(
      "until intents are set, workers connect with Discord's unprivileged set",
      int(list(f.sessions.values())[-1].identify["intents"]) == int(unprivileged),
      list(f.sessions.values())[-1].identify.get("intents"),
    )
    check(
      "GatewayControl reports what is in force",
      await GatewayControl(s.runtime).intents() == int(unprivileged),
    )

  wide = unprivileged | hikari.Intents.MESSAGE_CONTENT
  async with Stack(App(), intents=wide, extra_gateways=1) as s:
    f = s.fake
    control = GatewayControl(s.runtime)
    await f.until(lambda: f.identifies >= 1, 15)
    workers = [w for w in s.runtime.components if isinstance(w, GatewayWorker)]
    first = (await control.status()).desired
    assert first is not None
    check(
      "the generation carries the intents it connects with",
      first.intents == int(wide)
      and int(list(f.sessions.values())[-1].identify["intents"]) == int(wide),
      (first.intents, list(f.sessions.values())[-1].identify.get("intents")),
    )
    identified = f.identifies
    new = wide | hikari.Intents.GUILD_MEMBERS
    await control.set_intents("unprivileged,message_content,guild_members")
    check(
      "set_intents starts a new generation that identifies with them",
      await f.until(lambda: f.identifies > identified, 20)
      and int(list(f.sessions.values())[-1].identify["intents"]) == int(new),
      [x.identify.get("intents") for x in f.sessions.values()],
    )
    status = await control.status()
    check(
      "two workers, one change, one generation",
      status.desired is not None
      and status.desired.id == first.id + 1
      and status.desired.intents == int(new),
      status.desired,
    )
    check(
      "the new generation takes over once its shards are ready",
      await _until_async(
        lambda: control.status(),
        lambda st: st.active is not None and st.active.id == first.id + 1,
        20,
      ),
    )
    check(
      "every worker connects that generation with its intents",
      all(w.intents_for(first.id + 1) == new for w in workers),
    )
    generation = (await control.status()).desired
    await control.set_intents(int(new))
    check(
      "setting the intents already in force writes nothing",
      (await control.status()).desired == generation,
    )
    try:
      await control.set_intents("nonsense")
      refused = False
    except ValueError:
      refused = True
    check(
      "a typo is refused before anything is written",
      refused and (await control.status()).desired == generation,
    )
    after_reshard = await control.set_shard_count(1)
    check(
      "resharding keeps the intents",
      after_reshard.intents == int(new),
      after_reshard,
    )

    await control.configure(max_concurrency=2, lease_ttl=6.0)
    ok = await _until_async(
      lambda: asyncio.sleep(0, [w.max_concurrency for w in workers]),
      lambda values: values == [2, 2],
      10,
    )
    check("other settings follow the shared document", ok)
    config = await control.settings()
    check(
      "the gateway table holds every setting",
      set(config.value.model_dump())
      == {"shard_count", "intents", "max_concurrency", "lease_ttl", "presence"},
      config.value,
    )
    # Writing the table directly (as `micro configure` does) is enough: the workers
    # follow it and make a generation match.
    before = (await control.status()).desired
    assert before is not None
    await config.update(shard_count=2)
    check(
      "editing the table rolls a generation with the new shard count",
      await _until_async(
        lambda: control.status(),
        lambda st: (
          st.desired is not None
          and st.desired.id > before.id
          and st.desired.shard_count == 2
        ),
        20,
      ),
    )
    await control.update_presence(status="idle")
    presence = (await config.read()).value.presence
    check(
      "presence is a field of the same table",
      presence is not None and presence.status == "idle",
    )


async def _until_async(read: Any, ok: Any, timeout: float) -> bool:
  """Poll an async reader until `ok(value)`; the tests' stand-in for a watch."""
  deadline = time.monotonic() + timeout
  while time.monotonic() < deadline:
    if ok(await read()):
      return True
    await asyncio.sleep(0.05)
  return False


async def idle_scenarios() -> None:
  print("idle: an idle deployment does no work")
  async with Stack(App(), extra_gateways=1) as s:
    f = s.fake
    await f.until(lambda: s.names() == ["feedback", "hello", "slow"], 10)
    workers = [w for w in s.runtime.components if isinstance(w, GatewayWorker)]
    await f.until(lambda: all(w.ready for w in workers), 15)
    await asyncio.sleep(1)  # let the start-up churn settle
    counts = {w.name: 0 for w in workers}
    for worker in workers:
      original = worker._reconcile  # pyright: ignore[reportPrivateUsage]

      async def counted(original: Any = original, name: str = worker.name) -> None:
        counts[name] += 1
        await original()

      worker._reconcile = counted  # type: ignore[method-assign]  # pyright: ignore[reportPrivateUsage]
    await asyncio.sleep(4)
    # One pass every lease_ttl / 3 (3.3 s) per worker is the design; a feedback loop
    # (a lease renewal waking the loop that renews it) runs thousands of times a second.
    check(
      "an idle Gateway reconciles on its timer, not in a loop",
      all(count <= 6 for count in counts.values()),
      counts,
    )


async def sync_scenarios() -> None:
  print("sync: command registration under failure")
  async with Stack(App()) as s:
    f = s.fake
    await f.until(lambda: s.names() == ["feedback", "hello", "slow"], 10)
    puts = len(f.where("PUT", r"/commands$"))
    check("registered with one bulk overwrite", puts == 1, puts)
    await s.sync.sync()
    check(
      "an unchanged pass does not call Discord again",
      len(f.where("PUT", r"/commands$")) == puts,
    )

    want = ["feedback", "hello", "slow"]
    f.commands["global"] = []  # someone cleared them in the developer portal
    await s.sync.sync()
    check(
      "an ordinary pass trusts its record and does not poll Discord",
      s.names() == [],
      s.names(),
    )
    await s.sync.sync(verify=True)
    check(
      "a verifying pass (micro commands sync) repairs the drift",
      s.names() == want,
      s.names(),
    )

    f.commands["global"] = []
    await s.runtime.add(CommandSync("command-sync-restarted"))
    check(
      "a restarted CommandSync repairs drift on its first pass",
      await f.until(lambda: s.names() == want, 10),
      s.names(),
    )

  async with Stack(App(), guilds=("500",)) as s:
    f = s.fake
    f.rate_limit(r"/applications/\d+/commands$", retry_after=0.3, times=2)
    check(
      "429s on the bulk overwrite are retried",
      await f.until(lambda: s.names() == ["feedback", "hello", "slow"], 15),
      [c.status for c in f.where("PUT", r"/commands$")],
    )

  async with Stack(App(guild_commands=(666,)), guilds=("500",)) as s:
    f = s.fake
    f.forbidden_guilds.add("666")  # the bot was removed from this guild
    ok = await f.until(lambda: s.names() == ["feedback", "hello", "slow"], 12)
    check(
      "a guild the bot left does not block global commands",
      ok,
      [(c.path, c.status) for c in f.calls if "commands" in c.path],
    )

  async with Stack(App()) as s:
    from micro.discord.interactions import SYNC_LOCK, sync_commands

    async def consumers() -> int:
      return (await s.runtime.jetstream.account_info()).consumers

    await asyncio.sleep(2)
    before = await consumers()
    http = DiscordHTTPClient(s.runtime)
    application = str((await http.call("get_my_application"))["id"])
    locks = await s.runtime.locks()
    for _ in range(20):
      async with locks.hold(SYNC_LOCK, ttl=30):
        await sync_commands(s.runtime, http, application, verify=True)
    check(
      "table reads leave no consumers behind",
      (after := await consumers()) == before,
      (before, after),
    )
    await asyncio.sleep(6)  # presence refreshes; an idle CommandSync must not poll
    check(
      "an idle deployment does not accumulate consumers",
      (idle := await consumers()) == before,
      (before, idle),
    )


async def cli_scenarios() -> None:
  print("cli: the server and the nodes, as separate processes")
  from micro.launch import reachable

  bin_dir = ROOT / ".venv/bin"
  env = os.environ | {"PATH": f"{bin_dir}:{os.environ['PATH']}"}
  micro = [sys.executable, "-m", "micro"]
  procs: list[Any] = []

  def project(directory: Path, port: int) -> None:
    (directory / "micro.toml").write_text(
      f'name = "demo"\nnats = "nats://127.0.0.1:{port}"\n'
      '[processes.app]\ncomponents = ["services.*"]\nreplicas = 2\n'
    )
    (directory / "services/probe").mkdir(parents=True)
    (directory / "services/__init__.py").write_text("")
    (directory / "services/probe/__init__.py").write_text(
      "from micro.service import Service\n\nservice = Service('probe')\n"
    )

  async def cli(directory: Path, *args: str, merge: bool = True) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
      *micro,
      *args,
      cwd=directory,
      env=env,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.STDOUT if merge else asyncio.subprocess.DEVNULL,
    )
    out, _ = await asyncio.wait_for(proc.communicate(), 60)
    return proc.returncode or 0, out.decode()

  async def long_running(directory: Path, *args: str) -> Any:
    """Like a terminal's foreground job: its own process group, stopped with Ctrl-C."""
    proc = await asyncio.create_subprocess_exec(
      *micro,
      *args,
      cwd=directory,
      env=env,
      stdout=asyncio.subprocess.DEVNULL,
      stderr=asyncio.subprocess.DEVNULL,
      start_new_session=True,
    )
    procs.append(proc)
    return proc

  async def ctrl_c(proc: Any) -> int | None:
    os.killpg(proc.pid, signal.SIGINT)
    try:
      return await asyncio.wait_for(proc.wait(), 30)
    except TimeoutError:
      return None

  async def until(check: Callable[[], Awaitable[bool]], timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
      if await check():
        return True
      await asyncio.sleep(0.2)
    return await check()

  async def report(directory: Path) -> dict[str, Any]:
    code, out = await cli(directory, "nodes", "list", "--json", merge=False)
    return (
      json.loads(out) if code == 0 and out.strip() else {"nodes": {}, "components": []}
    )

  with tempfile.TemporaryDirectory() as raw:
    d = Path(raw)
    port = free_port()
    project(d, port)
    try:
      (d / "no-server.toml").write_text(
        (d / "micro.toml").read_text() + "\n[nats_server]\nenabled = false\n"
      )
      code, out = await cli(d, "dev", "--config", "no-server.toml")
      check(
        "dev without a server it may start says how to get one",
        code == 1 and "micro server start" in out,
        (code, out),
      )
      code, out = await cli(d, "server", "status")
      check(
        "server status with no server fails plainly",
        code == 1 and "No NATS server" in out,
        (code, out),
      )

      server = await long_running(d, "server", "start")
      check(
        "micro server start brings NATS up on its own",
        await until(lambda: reachable("127.0.0.1", port), 20),
      )
      code, out = await cli(d, "server", "start")
      check(
        "a second server start refuses",
        code == 1 and "already running" in out,
        (code, out),
      )
      code, out = await cli(d, "server", "status", merge=False)
      check(
        "server status reports JetStream", code == 0 and "streams" in out, (code, out)
      )

      code, out = await cli(d, "worker", "nope")
      check(
        "an unknown process group lists the ones micro.toml has",
        code == 1 and "No process group 'nope'" in out and "app" in out,
        (code, out),
      )
      with tempfile.TemporaryDirectory() as empty:
        code, out = await cli(Path(empty), "worker", "app")
        check(
          "a group name without a micro.toml says to run init",
          code == 1 and "micro init" in out,
          (code, out),
        )
      code, out = await cli(d, "worker")
      check(
        "a worker with nothing to host says so",
        code == 1 and "Nothing to host" in out,
        (code, out),
      )
      solo = await long_running(d, "worker", "app")
      async with Runtime(f"nats://127.0.0.1:{port}", name="watcher") as watcher:

        async def probe_present() -> bool:
          return any(e.name == "probe" for e in watcher.directory.entries())

        check(
          "a worker alone hosts its components against the server",
          await until(probe_present, 20),
        )
        check("Ctrl-C stops a worker cleanly", await ctrl_c(solo) == 0)

        async def probe_gone() -> bool:
          return not await probe_present()

        check(
          "a stopped worker leaves no components behind", await until(probe_gone, 10)
        )

      alpha = await long_running(d, "dev", "--name", "alpha")
      check(
        "a node starts against the running server and runs its processes",
        await until(lambda: _count(report(d), "alpha", 2)),
        None,
      )
      beta = await long_running(d, "dev", "--name", "beta")
      check(
        "a second node joins the same deployment",
        await until(lambda: _count(report(d), "beta", 2)),
        None,
      )

      async def both_listed() -> bool:
        body = await report(d)
        probes = [c for c in body["components"] if c["name"] == "probe"]
        return sorted(body["nodes"]) == ["alpha", "beta"] and len(probes) == 4

      check(
        "ps lists both nodes and their components",
        await until(both_listed),
        await report(d),
      )

      code, out = await cli(d, "dev", "--name", "alpha")
      check(
        "a node name can only run once",
        code == 1 and "already running" in out,
        (code, out),
      )
      code, out = await cli(d, "dev", "scale", "app", "3")
      check(
        "scale without --node is ambiguous with two nodes",
        code == 1 and "Several nodes" in out,
        (code, out),
      )
      code, out = await cli(d, "dev", "scale", "app", "3", "--node", "alpha")
      check("scale --node targets one node", code == 0, (code, out))
      body = await report(d)
      sizes = {n: len(v["processes"]) for n, v in body["nodes"].items()}
      check("only that node changed", sizes == {"alpha": 3, "beta": 2}, sizes)
      before = {c["pid"] for c in body["nodes"]["beta"]["processes"]}
      code, out = await cli(d, "dev", "roll", "app", "--node", "beta")
      after = {c["pid"] for c in (await report(d))["nodes"]["beta"]["processes"]}
      check(
        "roll replaces every process of that node",
        code == 0 and not (before & after) and len(after) == 2,
        (code, before, after),
      )

      check("Ctrl-C stops a node cleanly", await ctrl_c(alpha) == 0)
      check(
        "the server is still running after a node stopped",
        await reachable("127.0.0.1", port),
      )
      body = await report(d)
      check(
        "the other node carries on",
        sorted(body["nodes"]) == ["beta"],
        body["nodes"].keys(),
      )
      await ctrl_c(beta)
      check(
        "Ctrl-C stops the server on its own",
        await ctrl_c(server) == 0 and not await reachable("127.0.0.1", port),
      )
    finally:
      for proc in procs:
        if proc.returncode is None:
          with __import__("contextlib").suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)

  with tempfile.TemporaryDirectory() as raw:
    d = Path(raw)
    port = free_port()
    project(d, port)
    up = await long_running(d, "dev")
    try:
      check(
        "micro dev runs the server and the processes together",
        await until(lambda: _count(report(d), None, 2), 30)
        and await reachable("127.0.0.1", port),
      )
      code = await ctrl_c(up)
      check(
        "Ctrl-C stops the processes, then the server it started",
        code == 0 and not await reachable("127.0.0.1", port),
        code,
      )
    finally:
      if up.returncode is None:
        os.killpg(up.pid, signal.SIGKILL)

  here = Path(tempfile.gettempdir())
  for argv, word in (
    (("help", "dev"), "scale"),
    (("server", "--help"), "status"),
    (("dev", "scale", "--help"), "--node"),
    (("nodes", "list", "--help"), "--config"),
    (("services", "--help"), "add"),
    (("commands", "sync", "--help"), "--config"),
  ):
    code, out = await cli(here, *argv)
    check(
      f"micro {' '.join(argv)} shows its help",
      code == 0 and word in out,
      (code, out[-200:]),
    )
  from contextlib import redirect_stdout
  from io import StringIO

  from micro import cli as micro_cli

  root = micro_cli._parser()  # pyright: ignore[reportPrivateUsage]

  def walk(parser: Any, path: tuple[str, ...] = ()) -> Any:
    yield path, parser
    if (actions := parser.commands()) is not None:
      for name, child in actions.choices.items():
        yield from walk(child, (*path, name))

  everything = list(walk(root))
  groups = [(path, p) for path, p in everything if p.commands() is not None]
  leaves = [(path, p) for path, p in everything if p.commands() is None]
  check(
    "every command with subcommands ends in a `help` subcommand",
    all("help" in p.commands().choices for _, p in groups),
    [path for path, p in groups if "help" not in p.commands().choices],
  )
  check(
    "every command, group or leaf, takes -h/--help",
    all(any("-h" in a.option_strings for a in p._actions) for _, p in everything),  # pyright: ignore[reportPrivateUsage]
  )
  check(
    "leaves have only -h: no `help` subcommand",
    all(p.commands() is None for _, p in leaves),
  )
  bare_ok, help_ok, same_ok = [], [], []
  for path, group in groups:
    parsed = root.parse_args([*path])
    runs_itself = path == ("dev",)  # `micro dev` starts the bot; the rest show help
    bare_ok.append(
      runs_itself
      if runs_itself
      else parsed.handler is micro_cli._help_handler and parsed.target is group  # pyright: ignore[reportPrivateUsage]
    )
    asked = root.parse_args([*path, "help"])
    help_ok.append(asked.handler is micro_cli._help_handler and asked.target is group)  # pyright: ignore[reportPrivateUsage]
    shown = StringIO()
    with redirect_stdout(shown):
      await micro_cli._help_handler(asked)  # pyright: ignore[reportPrivateUsage]
    same_ok.append(shown.getvalue() == group.format_help())
  check(
    "a group run without a command falls back to its help",
    all(bare_ok),
    [g[0] for g, ok in zip(groups, bare_ok) if not ok],
  )
  check("`help` on every group shows that group's help", all(help_ok) and all(same_ok))
  code, out = await cli(here, "pkg")
  check(
    "micro pkg with no command shows its help and exits 0",
    code == 0 and "source" in out and "help" in out,
    out,
  )
  code, out = await cli(here, "pkg", "help", "source", "add")
  check(
    "`help` follows a path to a leaf",
    code == 0 and "--ref" in out and "name" in out,
    out,
  )
  code, out = await cli(here, "help", "pkg", "nope")
  check(
    "an unknown help topic says where to look",
    code == 1 and "No command 'nope'" in out and "micro pkg help" in out,
    out,
  )
  code, out = await cli(here, "--help")
  check(
    "the help is grouped",
    all(f"{title}:" in out for title in ("Project", "Run", "Discord")),
    out[:300],
  )
  # Commands read .env next to micro.toml (a regression once skipped it for every command).
  with tempfile.TemporaryDirectory() as raw:
    dotenv_dir = Path(raw)
    (dotenv_dir / "micro.toml").write_text('name = "dotenv"\n')
    (dotenv_dir / ".env").write_text(f"DISCORD_TOKEN={TOKEN}\n")
    saved = os.environ.pop("DISCORD_TOKEN", None)
    try:
      code, out = await cli(dotenv_dir, "invite")
    finally:
      if saved is not None:
        os.environ["DISCORD_TOKEN"] = saved
    check(
      "commands read DISCORD_TOKEN from .env",
      code == 0 and "client_id=100" in out,
      out[-200:],
    )
    code, out = await cli(dotenv_dir, "pkg")
    check(
      "and a help command does not need it", code == 0 and "source" in out, out[-200:]
    )


async def _count(
  body: Awaitable[dict[str, Any]], node: str | None, expected: int
) -> bool:
  nodes = (await body)["nodes"]
  if node is None:
    return any(len(v["processes"]) == expected for v in nodes.values())
  return node in nodes and len(nodes[node]["processes"]) == expected


async def _micro(directory: Path, *args: str, merge: bool = True) -> tuple[int, str]:
  env = os.environ | {"PATH": f"{ROOT / '.venv/bin'}:{os.environ['PATH']}"}
  proc = await asyncio.create_subprocess_exec(
    sys.executable,
    "-m",
    "micro",
    *args,
    cwd=directory,
    env=env,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT if merge else asyncio.subprocess.DEVNULL,
  )
  out, _ = await asyncio.wait_for(proc.communicate(), 60)
  return proc.returncode or 0, out.decode()


def _git(repo: Path, *args: str) -> str:
  done = subprocess.run(
    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
    cwd=repo, capture_output=True, text=True, check=True,
  )  # fmt: skip
  return done.stdout.strip()


def _commit(repo: Path, message: str, tag: str | None = None) -> str:
  _git(repo, "add", "-A")
  _git(repo, "commit", "-qm", message)
  if tag:
    _git(repo, "tag", tag)
  return _git(repo, "rev-parse", "HEAD")


def _upstream(root: Path) -> Path:
  """A git repository standing in for Micro's examples: the real hello, chat and
  ticker, plus a template and a package that has one file for every outcome."""
  repo = root / "upstream"
  repo.mkdir()
  _git(repo, "init", "-q", "-b", "main")
  for name in ("hello", "chat", "ticker"):
    shutil.copytree(
      ROOT / "packages" / name,
      repo / "packages" / name,
      ignore=shutil.ignore_patterns("__pycache__"),
    )
  tpl = repo / "packages/tpl"
  tpl.mkdir(parents=True)
  (tpl / "package.toml").write_text('description = "A template; name it."\n')
  (tpl / "__init__.py.tmpl").write_text(
    '"""The ${name} service."""\nname = "${name}"\n'
  )
  demo = repo / "packages/demo"
  demo.mkdir(parents=True)
  for name in (
    "plain", "edited", "both", "clash", "deleted", "gone", "same", "dropped", "orphan",
  ):  # fmt: skip
    (demo / f"{name}.py").write_text("a = 1\nb = 2\nc = 3\nd = 4\n")
  (demo / "__init__.py").write_text('"""A package with a file for every outcome."""\n')
  _commit(repo, "v1", tag="v1")
  return repo


def _release_two(repo: Path) -> str:
  """What the next release changes in demo."""
  demo = repo / "packages/demo"
  v2 = "a = 1\nb = 2\nc = 3\nd = 40\n"
  (demo / "plain.py").write_text("a = 10\nb = 2\nc = 3\nd = 4\n")
  (demo / "both.py").write_text(v2)  # you edit line a, they edit line d
  (demo / "clash.py").write_text("a = 1\nb = 22\nc = 3\nd = 4\n")  # same line as you
  (demo / "gone.py").write_text(v2)
  (demo / "same.py").write_text(v2)
  (demo / "dropped.py").unlink()
  (demo / "orphan.py").unlink()
  (demo / "extra.py").write_text("x = 1\n")
  return _commit(repo, "v2", tag="v2")


def _edit_demo(folder: Path) -> None:
  """Your edits to a fresh copy of demo."""
  (folder / "edited.py").write_text("a = 1\nb = 99\nc = 3\nd = 4\n")
  (folder / "both.py").write_text("a = 11\nb = 2\nc = 3\nd = 4\n")
  (folder / "clash.py").write_text("a = 1\nb = 77\nc = 3\nd = 4\n")
  (folder / "deleted.py").unlink()
  (folder / "gone.py").unlink()
  (folder / "same.py").write_text("a = 1\nb = 2\nc = 3\nd = 40\n")
  (folder / "orphan.py").write_text("a = 99\nb = 2\nc = 3\nd = 4\n")


async def pkg_scenarios() -> None:
  print("pkg: git sources, packages, and merging upgrades")
  from micro.scaffold import Project, _sources, packages
  from micro.scaffold import _git as scaffold_git

  saved = os.environ.get("MICRO_PACKAGES_URL")
  with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    repo = _upstream(root)
    os.environ["MICRO_PACKAGES_URL"] = repo.as_uri()
    first = _git(repo, "rev-parse", "HEAD")
    try:
      await _pkg_cli(root, repo, first)
      await _pkg_merging(root, repo, first, Project, packages)
      await _pkg_refs_and_sources(root, repo, first, Project, packages, _sources)
      await _pkg_environment(root, scaffold_git)
    finally:
      if saved is None:
        os.environ.pop("MICRO_PACKAGES_URL", None)
      else:
        os.environ["MICRO_PACKAGES_URL"] = saved


async def _pkg_cli(root: Path, repo: Path, first: str) -> None:
  d = root / "cli"
  d.mkdir()
  code, out = await _micro(d, "init")
  lock = (d / "micro.lock").read_text() if (d / "micro.lock").exists() else ""
  check(
    "init fetches hello and records its source, ref and commit",
    code == 0
    and (d / "services/hello/__init__.py").is_file()
    and "[hello]" in lock
    and f'commit = "{first}"' in lock
    and 'ref = "main"' in lock,
    out + lock,
  )
  code, out = await _micro(d, "pkg", "list")
  check(
    "pkg list shows the source, its commit, and what you have added",
    code == 0
    and "builtin" in out
    and first[:7] in out
    and "tpl" in out
    and "services/hello" in out,
    out,
  )
  code, out = await _micro(d, "pkg", "add", "builtin/chat")
  check(
    "pkg add copies a package",
    code == 0 and (d / "services/chat/__init__.py").is_file(),
    out,
  )
  code, out = await _micro(d, "pkg", "add", "builtin/ticker")
  check(
    "another package, by SOURCE/NAME",
    code == 0 and (d / "services/ticker/__init__.py").is_file(),
    out,
  )
  code, out = await _micro(d, "pkg", "add", "builtin/tpl", "tickets")
  text = (d / "services/tickets/__init__.py").read_text() if code == 0 else ""
  check("a template is filled in with its name", 'name = "tickets"' in text, out + text)
  code, out = await _micro(d, "pkg", "add", "builtin/tpl")
  check(
    "a template without a name says so",
    code == 1 and "give the copy a name" in out,
    out,
  )
  code, out = await _micro(d, "pkg", "add", "builtin/nope")
  check(
    "an unknown package lists the choices",
    code == 1 and "choose from" in out and "chat" in out,
    out,
  )
  code, out = await _micro(d, "pkg", "add", "builtin/chat")
  check("adding twice is refused", code == 1 and "already exists" in out, out)
  code, out = await _micro(d, "pkg", "status")
  check(
    "status: everything up to date, with the source and commit shown",
    code == 0
    and out.count("up to date") == 4
    and f"main ({first[:7]})".replace("main (", "builtin@main (") in out,
    out,
  )
  code, out = await _micro(d, "services", "add", "orders")
  check(
    "services add makes an empty service without any network",
    code == 0 and "Service(" in (d / "services/orders/__init__.py").read_text(),
    out,
  )
  code, out = await _micro(d, "services", "add", "Bad Name")
  check("a bad service name is refused", code == 1 and "lowercase" in out, out)
  code, out = await _micro(d, "services", "list")
  check(
    "services list says which came from a package and which are yours",
    code == 0 and "from hello (builtin)" in out and "orders" in out and "yours" in out,
    out,
  )
  code, out = await _micro(d, "pkg", "forget", "tickets")
  code, out = await _micro(d, "pkg", "status", "tickets")
  check(
    "an untracked name is an error", code == 1 and "Not an added package" in out, out
  )


async def _pkg_merging(root: Path, repo: Path, first: str, Project, packages) -> None:
  def fresh(name: str) -> tuple[Any, Path]:
    d = root / name
    (d / "services").mkdir(parents=True)
    project = Project(d, name, d / "services", "services.*")
    packages.add("builtin/demo", project, ref="v1")
    folder = d / "services/demo"
    _edit_demo(folder)
    return project, folder

  project, folder = fresh("merge")
  second = _release_two(repo)
  kinds = {c.file: c.kind for c in packages.status(project)[0].changes}
  want = {
    "plain.py": "upgrade", "edited.py": "modified", "both.py": "conflict",
    "clash.py": "conflict", "deleted.py": "deleted", "gone.py": "gone",
    "same.py": "refresh", "dropped.py": "remove", "orphan.py": "orphan",
    "extra.py": "add", "__init__.py": "current",
  }  # fmt: skip
  check(
    "status: pinned to the v1 tag, nothing moves",
    set(kinds.values()) <= {"modified", "deleted", "current"},
    kinds,
  )
  reports = packages.upgrade(project, ref="main")
  kinds = {c.file: c.kind for c in reports[0].changes}
  check(
    "upgrade --ref main follows the branch and classifies each file",
    kinds == {**want, "both.py": "merged", "clash.py": "markers"},
    {k: (kinds.get(k), v) for k, v in want.items() if kinds.get(k) != v},
  )
  text = lambda name: (folder / name).read_text() if (folder / name).exists() else None
  check(
    "upgrade: untouched file replaced, new file added, dropped file removed",
    text("plain.py") == "a = 10\nb = 2\nc = 3\nd = 4\n"
    and text("extra.py") == "x = 1\n"
    and text("dropped.py") is None,
  )
  check(
    "upgrade: your edits, deletions and an edited dropped file are kept",
    text("edited.py") == "a = 1\nb = 99\nc = 3\nd = 4\n"
    and text("deleted.py") is None
    and text("orphan.py") == "a = 99\nb = 2\nc = 3\nd = 4\n",
  )
  check(
    "a file you both changed on different lines is merged",
    text("both.py") == "a = 11\nb = 2\nc = 3\nd = 40\n",
    text("both.py"),
  )
  clash = text("clash.py") or ""
  check(
    "a file you both changed on the same line gets conflict markers",
    "<<<<<<< yours" in clash
    and "b = 77" in clash
    and "b = 22" in clash
    and ">>>>>>>" in clash,
    clash,
  )
  entry = packages.Lock.load(project).entries["demo"]
  check(
    "the lock follows the files to the new commit and ref, with the undecided still flagged",
    entry.commit == second and entry.ref == "main",
    (entry.commit, entry.ref),
  )
  after = {c.file: c.kind for c in packages.status(project)[0].changes}
  check(
    "status keeps flagging the markers and the deleted-but-changed file",
    after["clash.py"] == "markers" and after["gone.py"] == "gone",
    after,
  )
  (folder / "clash.py").write_text("a = 1\nb = 77\nc = 3\nd = 4\n")  # you resolve it
  (folder / "gone.py").write_text(
    "a = 1\nb = 2\nc = 3\nd = 40\n"
  )  # and bring gone back
  after = {c.file: c.kind for c in packages.status(project)[0].changes}
  check(
    "resolving the markers clears the flag",
    after["clash.py"] == "modified" and "markers" not in after.values(),
    after,
  )
  patch = packages.diff(project, "demo")
  check(
    "diff shows what still differs from upstream",
    "-b = 77" in patch and "+b = 22" in patch,
    patch[:200],
  )

  # --theirs and --mine, from a fresh copy.
  repo_reset = _git(repo, "rev-parse", "HEAD")
  project, folder = fresh("theirs")
  packages.upgrade(project, ref="main", settle="theirs")
  check(
    "--theirs takes upstream's file for every conflict and brings a deleted file back",
    (folder / "both.py").read_text() == "a = 1\nb = 2\nc = 3\nd = 40\n"
    and (folder / "clash.py").read_text() == "a = 1\nb = 22\nc = 3\nd = 4\n"
    and (folder / "gone.py").exists(),
  )
  entry = packages.Lock.load(project).entries["demo"]
  check(
    "once nothing is undecided the lock moves to the new commit",
    entry.commit == repo_reset
    and entry.ref == "main"
    and not any(r.attention for r in packages.status(project)),
    (entry.commit, repo_reset),
  )
  project, folder = fresh("mine")
  packages.upgrade(project, ref="main", settle="mine")
  after = {c.file: c.kind for c in packages.status(project)[0].changes}
  check(
    "--mine keeps your files and marks upstream's reviewed",
    (folder / "clash.py").read_text() == "a = 1\nb = 77\nc = 3\nd = 4\n"
    and not (folder / "gone.py").exists()
    and after["clash.py"] == "modified"
    and after["gone.py"] == "deleted",
    after,
  )

  # A lock from before commits were recorded has no original to merge against.
  project, folder = fresh("legacy")
  lock = project.root / "micro.lock"
  lock.write_text(
    "\n".join(
      line for line in lock.read_text().splitlines() if not line.startswith("commit")
    )
  )
  reports = packages.upgrade(project, ref="main")
  kinds = {c.file: c.kind for c in reports[0].changes}
  check(
    "without a recorded commit a both-changed file stays a conflict",
    kinds["both.py"] == "conflict"
    and "<<<<<<<" not in (folder / "both.py").read_text(),
    kinds,
  )


async def _pkg_refs_and_sources(
  root: Path, repo: Path, first: str, Project, packages, sources
) -> None:
  d = root / "sources"
  d.mkdir()
  code, out = await _micro(d, "init")
  # A second repository as a named source.
  team = root / "team"
  (team / "packages/billing").mkdir(parents=True)
  _git(team, "init", "-q", "-b", "main")
  (team / "packages/billing/__init__.py").write_text(
    '"""Invoices for the team."""\nv = 1\n'
  )
  _commit(team, "billing v1", tag="v1")
  code, out = await _micro(d, "pkg", "source", "add", "team", team.as_uri())
  check(
    "pkg source add saves the source and says what it found",
    code == 0
    and "billing" in out
    and "[sources.team]" in (d / "micro.toml").read_text(),
    out,
  )
  code, out = await _micro(d, "pkg", "source", "list")
  check(
    "pkg source list shows both", code == 0 and "builtin" in out and "team" in out, out
  )
  code, out = await _micro(d, "pkg", "add", "billing")
  check(
    "a bare name is refused: name the source",
    code == 1 and "SOURCE/NAME" in out and "builtin/billing" in out,
    out,
  )
  code, out = await _micro(d, "pkg", "add", "team/billing")
  lock = (d / "micro.lock").read_text()
  check(
    "SOURCE/NAME adds from that source and records it",
    code == 0 and 'source = "team"' in lock and f'url = "{team.as_uri()}"' in lock,
    out,
  )
  (team / "packages/billing/__init__.py").write_text(
    '"""Invoices for the team."""\nv = 2\n'
  )
  _commit(team, "billing v2")
  code, out = await _micro(d, "pkg", "status", "billing")
  check(
    "status sees the source's new commit",
    "upgrade available" in out and "team@main" in out,
    out,
  )
  code, out = await _micro(d, "pkg", "source", "remove", "team")
  code, out = await _micro(d, "pkg", "upgrade", "billing")
  check(
    "a package still upgrades after its source is removed from micro.toml (the lock remembers it)",
    code == 0 and "v = 2" in (d / "services/billing/__init__.py").read_text(),
    out,
  )
  # A folder source, and the older `[sources]` table.
  (d / "folder-pkgs/thing").mkdir(parents=True)
  (d / "folder-pkgs/thing/__init__.py").write_text('"""A folder package."""\n')
  code, out = await _micro(d, "pkg", "source", "add", "loc", "./folder-pkgs")
  code, out = await _micro(d, "pkg", "add", "loc/thing")
  check(
    "a folder works as a source",
    code == 0 and (d / "services/thing/__init__.py").is_file(),
    out,
  )
  (d / "micro.toml").write_text(
    (d / "micro.toml").read_text() + '\n[sources.old]\npath = "x"\n'
  )
  old = root / "oldstyle"
  old.mkdir()
  (old / "micro.toml").write_text('[sources]\nteam = "team-packages"\n')
  check(
    "the older `[sources] name = folder` form still reads",
    sources.configured(old)["team"].path == "team-packages",
  )
  code, out = await _micro(d, "pkg", "source", "remove", "nope")
  check(
    "removing an unknown source says so", code == 1 and "no source named" in out, out
  )
  # Refs: a tag pins, a branch follows.
  code, out = await _micro(d, "pkg", "add", "builtin/ticker", "--ref", "v1")
  lock = (d / "micro.lock").read_text()
  check("--ref pins a tag and records it", code == 0 and 'ref = "v1"' in lock, out)
  code, out = await _micro(d, "pkg", "add", "builtin/hello", "hello2", "--ref", "nope")
  check("an unknown ref is an error", code == 1 and "nope" in out, out)
  code, out = await _micro(d, "pkg", "upgrade", "--ref", "main")
  check("--ref needs exactly one package", code == 1 and "name it" in out, out)


async def _pkg_environment(root: Path, scaffold_git) -> None:
  remotes = scaffold_git.remotes
  check(
    "https and ssh remotes are each other's fallback",
    remotes("https://github.com/o/r.git")
    == ["https://github.com/o/r.git", "git@github.com:o/r.git"]
    and remotes("git@github.com:o/r.git")
    == ["git@github.com:o/r.git", "https://github.com/o/r.git"]
    and remotes("ssh://git@gitlab.com/g/p")
    == ["ssh://git@gitlab.com/g/p", "https://gitlab.com/g/p.git"]
    and remotes("file:///x") == ["file:///x"],
  )
  # Offline: init still works, and says how to get hello later.
  d = root / "offline"
  d.mkdir()
  os.environ["MICRO_PACKAGES_URL"] = (root / "nowhere").as_uri()
  code, out = await _micro(d, "init")
  check(
    "init works without reaching the source, and says how to add hello",
    code == 0
    and (d / "micro.toml").is_file()
    and not (d / "services/hello").exists()
    and "micro pkg add builtin/hello" in out,
    out,
  )
  code, out = await _micro(d, "pkg", "add", "builtin/hello")
  check(
    "an unreachable source is a message, not a traceback",
    code == 1 and "Cannot reach" in out and "Traceback" not in out,
    out,
  )
  # No git at all.
  empty = root / "nogit"
  empty.mkdir()
  env_path = os.environ["PATH"]
  os.environ["PATH"] = str(empty)
  try:
    d2 = root / "nogit-project"
    d2.mkdir()
    code, out = await _micro(d2, "init")
  finally:
    os.environ["PATH"] = env_path
  check(
    "without git, init still works and `pkg` explains what to install",
    code == 0 and (d2 / "micro.toml").is_file() and "needs git" in out,
    out,
  )


async def service_scenarios() -> None:
  print("service: middleware on requests, events and work")
  from micro.errors import RemoteError
  from micro.service import Call, EventSchema, RequestSchema, WorkQueue

  class Say(BaseModel):
    text: str

  ECHO = RequestSchema[Say, str](id="mw.echo", input=Say, output=str)
  SECRET = RequestSchema[Say, str](id="mw.secret.read", input=Say, output=str)
  OTHER = RequestSchema[Say, str](id="mw.other", input=Say, output=str)
  HAPPENED = EventSchema[Say](id="mw.happened", payload=Say)
  QUEUE = WorkQueue[Say]("mw.jobs", Say)

  trace: list[str] = []
  flaky = {"left": 1}
  service = Service("mw")

  @service.use
  async def outer(call: Call, next: Any) -> None:
    trace.append(f"outer>{call.kind}:{call.key}")
    await next()
    trace.append(f"outer<{call.kind}:{call.key}")

  @service.use
  async def shout(call: Call, next: Any) -> None:
    if call.kind == "request" and call.key == "mw.echo":
      call.input = Say(text=call.input.text.upper())  # rewrite what the handler gets
    await next()
    if call.kind == "request" and call.key == "mw.echo":
      call.output = f"{call.output}!"  # rewrite what the caller gets

  @service.use("mw.secret")
  async def gate(call: Call, next: Any, end: Any) -> None:
    if call.input.text != "please":
      call.output = "denied"
      return await end()
    await next()

  @service.use("mw.other")
  async def forgets(call: Call, next: Any, end: Any) -> None:
    await end()  # ends without setting an output

  @service.use("mw.happened")
  async def veto(call: Call, next: Any, end: Any) -> None:
    if call.input.text == "skip":
      return await end()
    await next()

  @service.handle(ECHO)
  async def echo(request: Say) -> str:
    return request.text

  @service.handle(SECRET)
  async def secret(request: Say) -> str:
    return "the secret"

  @service.handle(OTHER)
  async def other(request: Say) -> str:
    return "unreachable"

  @service.listen(HAPPENED)
  async def happened(event: Say) -> None:
    trace.append(f"event:{event.text}")
    if event.text == "flaky" and flaky["left"]:
      flaky["left"] -= 1
      raise RuntimeError("try again")

  @service.work(QUEUE)
  async def job(item: Say) -> None:
    trace.append(f"job:{item.text}")

  async with Stack(App()) as s:
    await s.runtime.add(service)
    client = service.client
    check(
      "input and output rewritten", await client.request(ECHO, Say(text="hi")) == "HI!"
    )
    check(
      "scoped middleware passes the right input",
      await client.request(SECRET, Say(text="please")) == "the secret",
    )
    check(
      "end() with an output answers the caller",
      await client.request(SECRET, Say(text="nope")) == "denied",
    )
    try:
      await client.request(OTHER, Say(text="x"))
      code = None
    except RemoteError as error:
      code = error.code
    check("end() with no output is an error", code == "ended_without_reply", code)
    check(
      "middleware nests in order",
      trace[:2] == ["outer>request:mw.echo", "outer<request:mw.echo"],
      trace[:2],
    )
    trace.clear()
    await client.emit(HAPPENED, Say(text="skip"))
    await client.emit(HAPPENED, Say(text="ok"))
    await s.fake.until(lambda: "event:ok" in trace, 8)
    await asyncio.sleep(0.3)
    check("end() on an event skips its handler", "event:skip" not in trace, trace)
    check(
      "end() on an event is acked, not redelivered",
      trace.count("outer<event:mw.happened") == 2,
      trace,
    )
    trace.clear()
    await client.emit(HAPPENED, Say(text="flaky"))
    await s.fake.until(lambda: trace.count("event:flaky") >= 2, 12)
    check(
      "a failing handler still retries through middleware",
      trace.count("event:flaky") == 2,
      trace,
    )
    trace.clear()
    await client.enqueue(QUEUE, Say(text="a"))
    await s.fake.until(lambda: "job:a" in trace, 8)
    check("work runs through middleware", "outer>work:mw.jobs" in trace, trace)


class SignedRoute(Route):
  """A custom route: `sig.<anything>!` carries `n` before the bang."""

  prefix = "sig."

  def match(self, custom_id: str) -> dict[str, str] | None:
    if custom_id.startswith("sig.") and custom_id.endswith("!"):
      return {"n": custom_id[4:-1]}
    return None

  def dump(self) -> JsonValue:
    return {}

  @classmethod
  def load(cls, data: Any) -> SignedRoute:
    return cls()


async def route_scenarios() -> None:
  print("routes: declared custom ID routes (template, regex, custom, legacy)")
  from micro.runtime import _consumer as consumer_module

  consumer_module._FETCH_WAIT = 0.5  # pyright: ignore[reportPrivateUsage]
  from micro.discord.interactions import PatternRoute
  from micro.discord.interactions._pattern import literal_head

  check("literal head of a regex", literal_head(r"ticket\.(?P<a>\w+)") == "ticket.")
  check("quantified literal is not part of the head", literal_head(r"abc?d") == "ab")
  check("no head for a leading class", literal_head(r"\d+x") == "")
  check("template prefix", PatternRoute.template("a.{b}:{c}").prefix == "a.")

  service = Service("panel")
  components = Components(service)

  def says(text: str) -> Callable[[Interaction], Awaitable[None]]:
    async def handler(ctx: Interaction) -> None:
      await ctx.respond(f"{text} {dict(ctx.route)}")

    return handler

  components.match("ticket.{action}:{id:\\d+}")(says("template"))
  components.match(re.compile(r"report\.(?P<kind>spam|abuse)"))(says("regex"))
  components.match(SignedRoute())(says("custom"))
  components.match(CustomId("legacy"))(says("legacy"))

  async with Stack(App()) as s:
    await s.runtime.add(service)
    await s.fake.until(lambda: len(s.runtime.directory.entries("service")) >= 4, 8)
    f = s.fake
    cases = [
      ("ticket.close:42", "template", {"action": "close", "id": "42"}),
      ("report.spam", "regex", {"kind": "spam"}),
      ("sig.77!", "custom", {"n": "77"}),
      ("legacy:anything", "legacy", {}),
    ]
    for custom_id, word, params in cases:
      calls = await s.interact(f.component(custom_id))
      _, data = reply_of(calls)
      content = data.get("content", "")
      check(
        f"{custom_id} -> {word}",
        content.startswith(word) and str(params) in content,
        content,
      )
    calls = await s.interact(f.component("ticket.close:nope"))
    _, data = reply_of(calls)
    check(
      "a non-matching ID is unavailable, not misrouted",
      "isn't available" in data.get("content", ""),
      data,
    )

    slow: list[tuple[str, float]] = []
    for _ in range(2):
      # Idle for several fetch cycles (the stall this guards against follows a timed-out
      # fetch), with the cycle shortened so that takes seconds, not a minute.
      await asyncio.sleep(consumer_module._FETCH_WAIT * 2.4)  # pyright: ignore[reportPrivateUsage]
      for custom_id in ("ticket.close:42", "legacy:x", "ticket.close:42"):
        started = time.monotonic()
        await s.interact(f.component(custom_id))
        took = (
          time.monotonic() - started - 0.1
        )  # interact() waits 0.1 s after the reply
        if took > 0.5:
          slow.append((custom_id, round(took, 2)))
    check("the first click after idle is answered promptly", not slow, slow)


async def health_scenarios() -> None:
  print("health: the bundled introspection package")
  import importlib.util

  spec = importlib.util.spec_from_file_location(
    "health_package", ROOT / "packages/health/__init__.py"
  )
  assert spec and spec.loader
  health = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(health)

  async with Stack(App()) as s:
    await s.runtime.add(health.service)
    f = s.fake
    await f.until(lambda: "health" in s.names(), 10)
    data = await health.report(s.runtime)
    for _ in range(100):  # two reads at two moments: retry until they describe one
      if data["consumers"] == sum(item["consumers"] for item in data["streams"]):
        break
      await asyncio.sleep(0.05)
      data = await health.report(s.runtime)
    names = [item["stream"] for item in data["streams"]]
    check("report lists the streams", "MICRO_EVENTS" in names, names)
    check(
      "report counts match the account",
      data["consumers"] == sum(item["consumers"] for item in data["streams"]),
      data,
    )
    calls = await s.interact(f.slash("health"), count=2)
    texts = [str(c.body) for c in calls if c.body]
    check(
      "/health answers with a table",
      any("MICRO_EVENTS" in text and "consumers in total" in text for text in texts),
      texts,
    )


async def ui_scenarios() -> None:
  print("ui: every component, validated against Discord's own request models")
  from micro.discord import ui
  from micro.discord.ui import (
    EPHEMERAL,
    IS_COMPONENTS_V2,
    ActionRow,
    Button,
    ChannelSelect,
    Checkbox,
    CheckboxGroup,
    Container,
    Default,
    Emoji,
    File,
    FileUpload,
    GroupOption,
    Label,
    MediaGallery,
    MediaItem,
    MentionableSelect,
    Modal,
    RadioGroup,
    RoleSelect,
    Section,
    SelectOption,
    Separator,
    StringSelect,
    TextDisplay,
    TextInput,
    Thumbnail,
    UserSelect,
    embed,
    message_body,
  )  # fmt: skip

  problems: list[tuple[str, str]] = []
  count = [0]

  def case(name: str, components: Any, modal: bool = False) -> None:
    count[0] += 1
    try:
      ui.validate(components, modal=modal)
    except ValueError as error:
      problems.append((name, str(error)[:200]))

  # --- message components, every field
  case(
    "button primary",
    Button("Go", custom_id="a", style="primary", emoji="🙂", disabled=True, id=1),
  )
  for st in ("secondary", "success", "danger"):
    case(f"button {st}", Button("x", custom_id="a", style=st))
  case("button custom emoji", Button("x", custom_id="a", emoji="<a:wave:1234567890>"))
  case("button link", Button("Docs", url="https://example.com/x", emoji=Emoji("📖")))
  case("button premium", Button(sku_id=123456789012345678))
  case(
    "action row of buttons",
    ActionRow(*[Button(str(i), custom_id=f"b{i}") for i in range(5)], id=2),
  )
  opts = [
    SelectOption("A", "a", "first", True, "🅰"),
    "b",
    SelectOption("C", "c", emoji="<:c:123456789>"),
  ]
  case(
    "string select",
    ActionRow(StringSelect("s", opts, "pick", 1, 2, disabled=False, id=3)),
  )
  case("user select", ActionRow(UserSelect("u", "who", 1, 3, defaults=[1, 2])))
  case("role select", ActionRow(RoleSelect("r", defaults=[Default.role(5)])))
  case(
    "mentionable select",
    ActionRow(MentionableSelect("m", defaults=[Default.user(1), Default.role(2)])),
  )
  case(
    "channel select",
    ActionRow(
      ChannelSelect(
        "c",
        channel_types=[
          "text",
          "voice",
          "category",
          "announcement",
          "public_thread",
          "forum",
        ],
        defaults=[9],
      )
    ),
  )
  # --- v2
  case("text display", TextDisplay("**hi** there", id=10))
  case(
    "thumbnail",
    Section(
      "a",
      "b",
      TextDisplay("c"),
      accessory=Thumbnail("https://e.com/i.png", "alt", True),
    ),
  )
  case("section + button", Section("click", accessory=Button("Go", custom_id="x")))
  case(
    "media gallery",
    MediaGallery("https://e.com/a.png", MediaItem("attachment://b.png", "desc", True)),
  )
  case("file", File("attachment://report.pdf", spoiler=True))
  case("separator", [Separator(), Separator(divider=False, spacing="large")])
  case(
    "container",
    Container(
      TextDisplay("hello"),
      Separator(),
      Section("s", accessory=Thumbnail("https://e.com/i.png")),
      MediaGallery("https://e.com/a.png"),
      File("attachment://f.txt"),
      ActionRow(Button("b", custom_id="b")),
      Button("loose", custom_id="l"),
      UserSelect("loose-select"),
      accent_colour=0xFF8800,
      spoiler=True,
    ),
  )
  # --- modal
  case(
    "modal label+text",
    Label(
      "Name",
      TextInput(
        "name",
        style="paragraph",
        placeholder="p",
        value="v",
        min_length=1,
        max_length=50,
        required=False,
      ),
      "your name",
    ),
    modal=True,
  )
  case(
    "modal string select",
    Label("Pick", StringSelect("p", ["x", "y"], required=True)),
    modal=True,
  )
  case("modal user select", Label("User", UserSelect("u", defaults=[1])), modal=True)
  case("modal role select", Label("Role", RoleSelect("r")), modal=True)
  case(
    "modal mentionable",
    Label("Mention", MentionableSelect("m", defaults=[Default.role(1)])),
    modal=True,
  )
  case(
    "modal channel select",
    Label("Chan", ChannelSelect("c", channel_types=["text"])),
    modal=True,
  )
  case(
    "modal file upload",
    Label("Files", FileUpload("f", 1, 3, False, [".png", ".jpg"])),
    modal=True,
  )
  case(
    "modal radio",
    Label(
      "One",
      RadioGroup("rg", [GroupOption("A", "a", "d", True), "b", "c"], required=True),
    ),
    modal=True,
  )
  case(
    "modal checkbox group",
    Label("Many", CheckboxGroup("cg", ["a", GroupOption("B", "b")], 0, 2, False)),
    modal=True,
  )
  case("modal checkbox", Label("Agree", Checkbox("ck", default=True)), modal=True)
  case("modal text display", TextDisplay("Read this first"), modal=True)
  # --- whole modal
  m = Modal(
    "form",
    "Everything",
    [
      TextDisplay("intro"),
      Label("Name", TextInput("n")),
      Label("Role", RoleSelect("r")),
      Label("Opts", CheckboxGroup("c", ["a", "b"])),
      Label("Go?", Checkbox("g")),
    ],
  )
  case("whole modal", m.to_dict()["components"], modal=True)
  legacy = Modal("old", "Legacy", [TextInput("t", "Label")]).to_dict()
  case("legacy bare TextInput", legacy["components"], modal=True)

  check(
    f"{count[0]} component payloads are valid, every type with its fields",
    not problems,
    problems,
  )
  body = message_body(components=[Container(TextDisplay("x"))], ephemeral=True)
  check(
    "layout components set IS_COMPONENTS_V2 (and ephemeral still works)",
    body["flags"] == (EPHEMERAL | IS_COMPONENTS_V2),
    body,
  )
  rejected = 0
  for extra in ({"content": "hi"}, {"embeds": [embed("t")]}):
    try:
      message_body(components=[TextDisplay("x")], **extra)  # pyright: ignore[reportArgumentType]
    except ValueError:
      rejected += 1
  check("a layout message with content or embeds is refused early", rejected == 2)
  check(
    "a classic message sets no v2 flag",
    "flags" not in message_body("hi", components=[Button("b", custom_id="b")]),
  )
  refused = []
  for label, make in (
    ("premium with a label", lambda: Button("x", sku_id=1)),
    ("two targets", lambda: Button("x", custom_id="a", url="https://e.com")),
    ("file without attachment://", lambda: File("https://e.com/x")),
    (
      "bare TextInput without a label",
      lambda: Modal("m", "t", [TextInput("x")]).to_dict(),
    ),
  ):
    try:
      make()
    except ValueError:
      refused.append(label)
  check("invalid builders are refused at construction", len(refused) == 4, refused)
  from micro.discord.interactions import Interaction

  def interaction_of(data: dict[str, Any], kind: int = 5) -> Interaction:
    payload = {
      "id": "1",
      "token": "t",
      "application_id": "1",
      "type": kind,
      "data": data,
    }
    return Interaction(payload, None)  # type: ignore[arg-type]

  people = {
    "10": {"id": "10", "username": "ann"},
    "11": {"id": "11", "username": "bob"},
  }

  def field(kind: int, custom_id: str, **value: Any) -> dict[str, Any]:
    return {"type": 18, "component": {"type": kind, "custom_id": custom_id, **value}}

  submitted = interaction_of(
    {
      "custom_id": "form",
      "components": [
        {"type": 10},
        field(4, "name", value="Ada"),
        field(3, "color", values=["red", "blue"]),
        field(5, "who", values=["10", "11"]),
        field(6, "role", values=["20"]),
        field(8, "chan", values=["30"]),
        field(19, "files", values=["40", "41"]),
        field(21, "radio", value="b"),
        field(21, "radio_none", value=None),
        field(22, "boxes", values=["x", "z"]),
        field(23, "agree", value=True),
        {"type": 1, "components": [{"type": 4, "custom_id": "legacy", "value": "old"}]},
      ],
      "resolved": {
        "users": people,
        "members": {"10": {"roles": ["20"], "nick": "A"}},
        "roles": {"20": {"id": "20", "name": "mods"}},
        "channels": {"30": {"id": "30", "type": 0, "name": "general"}},
        "attachments": {
          "40": {"id": "40", "filename": "a.png", "size": 5},
          "41": {"id": "41", "filename": "b.txt", "size": 7},
        },
      },
    }
  )
  check(
    "a modal submission: every field type reads back, through labels and rows",
    submitted.inputs
    == {
      "name": "Ada",
      "color": ["red", "blue"],
      "who": ["10", "11"],
      "role": ["20"],
      "chan": ["30"],
      "files": ["40", "41"],
      "radio": "b",
      "radio_none": None,
      "boxes": ["x", "z"],
      "agree": True,
      "legacy": "old",
    },
    submitted.inputs,
  )
  check(
    "fields keeps to text inputs and radios, as strings",
    submitted.fields
    == {"name": "Ada", "radio": "b", "radio_none": "", "legacy": "old"},
    submitted.fields,
  )
  check(
    "selected entities resolve to typed objects",
    [u.username for u in submitted.users("who")] == ["ann", "bob"]
    and [m.nick for m in submitted.members("who")] == ["A"]
    and [r.name for r in submitted.roles("role")] == ["mods"]
    and [c.name for c in submitted.channels("chan")] == ["general"]
    and [(a.filename, a.size) for a in submitted.attachments("files")]
    == [("a.png", 5), ("b.txt", 7)]
    and submitted.choices("color") == ["red", "blue"],
  )
  menu = interaction_of(
    {
      "custom_id": "pick",
      "component_type": 7,
      "values": ["10", "20"],
      "resolved": {
        "users": {"10": people["10"]},
        "roles": {"20": {"id": "20", "name": "mods"}},
      },
    },
    kind=3,
  )
  check(
    "a mentionable select gives users and roles from ctx directly",
    [u.username for u in menu.users()] == ["ann"]
    and [r.name for r in menu.roles()] == ["mods"],
  )
  from pydantic import ValidationError

  from micro.discord.objects import User

  user = {
    "id": "1", "username": "ann", "avatar": None, "discriminator": "0",
    "public_flags": 0, "flags": 0, "global_name": None, "primary_guild": None,
    "accent_color": 123,
  }  # fmt: skip
  full = User.model_validate(user).full()
  try:
    User(id="1").full()
    partial_refused = False
  except ValidationError:
    partial_refused = True
  check(
    "a view's other fields stay on it, and .full() gives Discord's typed model",
    User.model_validate(user).accent_color == 123  # type: ignore[attr-defined]
    and type(full).__name__ == "UserResponse"
    and partial_refused,
  )
  try:
    ui.validate(Button("x", custom_id="a" * 101))
    caught = False
  except ValueError as error:
    caught = "at most 100" in str(error)
  check("validate() reports Discord's own limits", caught)


async def api_scenarios() -> None:
  print("api: every operation as a method, checked on the wire")
  import inspect
  from email import message_from_bytes
  from email.policy import default as email_policy

  import httpx2
  from pydantic import ValidationError

  from micro.discord import ui

  # Structure: every operation is a method whose parameters match its request model.
  from micro.discord._api import _body_fields  # pyright: ignore[reportPrivateUsage]
  from micro.discord.api import DiscordAPI, Upload
  from micro.discord.http_operations import HTTP_OPERATIONS
  from micro.discord.http_service import DiscordAPIError

  gaps: list[str] = []
  for op in HTTP_OPERATIONS.values():
    method = getattr(DiscordAPI, op.id, None)
    if method is None:
      gaps.append(f"{op.id}: missing")
      continue
    params = inspect.signature(method).parameters
    request = op.request_model.model_fields
    positional = [
      n
      for n, p in params.items()
      if n not in ("self", "body", "content") and p.kind is p.POSITIONAL_OR_KEYWORD
    ]
    if positional != list(op.path_fields):
      gaps.append(f"{op.id}: positional {positional} != {list(op.path_fields)}")
    wanted = (
      set(_body_fields(request["query"].annotation)) if "query" in request else set()
    )
    if "body" in request and "body" not in params:  # a list body is the `body` argument
      wanted |= {
        name
        for name, info in _body_fields(request["body"].annotation).items()
        if "root" not in name and not (info.alias or "").startswith("files[")
      }
    for name in wanted:
      if name not in params and name + "_" not in params:
        gaps.append(f"{op.id}: {name} missing")
    if op.method != "GET" and "reason" not in params:
      gaps.append(f"{op.id}: no reason=")
  check(
    f"all {len(HTTP_OPERATIONS)} operations are methods taking their path, query and body fields",
    not gaps,
    gaps[:6],
  )

  # Every ref method calls its operation with the ref's ids in the right places.
  import dataclasses

  import gen_api  # scripts/gen_api.py: the table the refs were generated from

  from micro.discord import refs as ref_module
  from micro.discord.http_operations import HTTP_OPERATIONS as OPS

  class Recorder:
    def __init__(self) -> None:
      self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str) -> Any:
      async def record(*args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))

      return record

  wrong: list[str] = []
  total = 0
  for ref_name, spec in gen_api.REFS.items():
    ref_class = getattr(ref_module, ref_name)
    recorder = Recorder()
    ids = [f"ID{n}" for n in range(len(spec.ids))]
    ref = ref_class(recorder, *ids)
    for method_name, entry in spec.methods.items():
      op_id = entry if isinstance(entry, str) else entry[0]
      operation = OPS[op_id]  # pyright: ignore[reportArgumentType]  # type: ignore[index]
      method = getattr(ref, method_name)
      sig = inspect.signature(method)
      args = [
        f"ARG{n}"
        for n, p in enumerate(sig.parameters.values())
        if p.kind is p.POSITIONAL_OR_KEYWORD
      ]
      kwargs = {
        n: "KW"
        for n, p in sig.parameters.items()
        if p.kind is p.KEYWORD_ONLY and p.default is p.empty
      }
      recorder.calls.clear()
      await method(*args, **kwargs)
      total += 1
      called, positional, _ = recorder.calls[-1]
      expected_positional = []
      free = iter(args)
      for field_name in operation.path_fields:
        expected_positional.append(
          ids[spec.ids.index(field_name)] if field_name in spec.ids else next(free)
        )
      if (
        called != op_id
        or list(positional[: len(expected_positional)]) != expected_positional
      ):
        wrong.append(
          f"{ref_name}.{method_name}: {called}{positional} != {op_id}{tuple(expected_positional)}"
        )
    for link, (target, new_ids) in spec.links.items():
      made = getattr(ref, link)(*[f"N{n}" for n in range(len(new_ids))])
      total += 1
      if type(made).__name__ != target or [
        getattr(made, i) for i in gen_api.REFS[target].ids
      ] != [*ids, *[f"N{n}" for n in range(len(new_ids))]]:
        wrong.append(f"{ref_name}.{link}")
    if {f.name for f in dataclasses.fields(ref_class)} != {"api", *spec.ids}:
      wrong.append(f"{ref_name}: fields")
  check(
    f"all {total} ref methods call their operation with the ref's ids bound in place",
    not wrong and total > 100,
    wrong[:4],
  )

  seen: list[dict[str, Any]] = []
  answers: dict[str, tuple[int, Any]] = {}

  def discord(request: httpx2.Request) -> httpx2.Response:
    seen.append(
      {
        "method": request.method,
        "path": request.url.path.removeprefix("/api/v10"),
        "query": dict(request.url.params),
        "headers": dict(request.headers),
        "body": request.content,
      }
    )
    status, body = answers.get(f"{request.method} {seen[-1]['path']}", (204, None))
    headers = {"via": "1.1 google"} if status == 429 else {}
    return (
      httpx2.Response(status, json=body, headers=headers)
      if body is not None
      else httpx2.Response(status, headers=headers)
    )

  def json_of(call: dict[str, Any]) -> Any:
    return json.loads(call["body"])

  port = free_port()
  binary = shutil.which("nats-server") or str(ROOT / ".venv/bin/nats-server")
  with tempfile.TemporaryDirectory() as store:
    server = await asyncio.create_subprocess_exec(
      binary, "-js", "-p", str(port), "-sd", store,
      stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )  # fmt: skip
    try:
      await wait_listening(port)
      async with Runtime(
        f"nats://127.0.0.1:{port}", name="api", storage=StorageType.MEMORY
      ) as runtime:
        http_worker = DiscordHTTPWorker(
          TOKEN,
          transport=httpx2.MockTransport(discord),
          api_url="http://discord.test/api/v10",
        )
        hooked: list[Any] = []
        late: list[Any] = []

        async def late_hook(event: Any) -> None:
          late.append(event)
          raise RuntimeError("hooks must not break requests")

        http_worker.hook(hooked.append)
        unhook = http_worker.hook(late_hook)
        await runtime.add(http_worker)
        await runtime.directory.wait_for(lambda d: bool(d.entries(http_worker.kind)))
        api = DiscordHTTPClient(runtime).api

        message = {
          "id": "9", "channel_id": "5", "content": "hi", "components": [],
          "author": {"id": "1", "username": "bot", "avatar": None, "discriminator": "0", "public_flags": 0, "flags": 0, "global_name": None, "primary_guild": None},
          "attachments": [], "embeds": [], "mentions": [], "mention_roles": [], "pinned": False,
          "mention_everyone": False, "tts": False, "timestamp": "2024-01-01T00:00:00+00:00",
          "edited_timestamp": None, "flags": 0, "type": 0,
        }  # fmt: skip
        answers["POST /channels/5/messages"] = (200, message)
        sent = await api.create_message(
          5,
          content="@everyone hello",
          embeds=[
            ui.embed(
              "T",
              "D",
              timestamp="2024-01-01T00:00:00+00:00",
              footer="f",
              footer_icon="https://e.com/i.png",
            )
          ],
          components=[
            ui.Button("Go", custom_id="go"),
            ui.StringSelect("s", ["a", "b"]),
          ],
        )
        call = seen[-1]
        body = json_of(call)
        check(
          "create_message: a typed message comes back",
          getattr(sent, "content", None) == "hi"
          and type(sent).__name__ == "MessageResponse",
          type(sent),
        )
        check(
          "create_message: path, JSON body, builders laid out into rows",
          call["method"] == "POST"
          and call["path"] == "/channels/5/messages"
          and body["content"] == "@everyone hello"
          and [row["type"] for row in body["components"]] == [1, 1]
          and body["embeds"][0]["footer"]["icon_url"] == "https://e.com/i.png",
          body,
        )
        check(
          "create_message: mentions are safe unless you say otherwise",
          body["allowed_mentions"] == {"parse": [], "replied_user": False},
          body.get("allowed_mentions"),
        )
        await api.create_message(
          5, components=[ui.Container(ui.TextDisplay("hi"), accent_colour=0xFF0000)]
        )
        body = json_of(seen[-1])
        check(
          "create_message: layout components set IS_COMPONENTS_V2 on their own",
          body["flags"] & ui.IS_COMPONENTS_V2 and body["components"][0]["type"] == 17,
          body,
        )
        await api.create_message(
          5,
          content="with files",
          embeds=[ui.embed("T")],
          files=[
            Upload("cat.png", b"\x89PNG-data", "image/png"),
            Upload("notes.txt", b"plain"),
          ],
          reason="because",
        )
        call = seen[-1]
        envelope = message_from_bytes(
          b"Content-Type: "
          + call["headers"]["content-type"].encode()
          + b"\r\n\r\n"
          + call["body"],
          policy=email_policy,
        )
        parts = {
          part.get_param("name", header="content-disposition"): part
          for part in envelope.iter_parts()
        }
        payload = json.loads(parts["payload_json"].get_content())
        check(
          "create_message with files: multipart, payload_json for the rest, real file names",
          call["headers"]["content-type"].startswith("multipart/form-data")
          and payload["content"] == "with files"
          and payload["embeds"][0]["title"] == "T"
          and parts["files[0]"].get_filename() == "cat.png"
          and parts["files[0]"].get_content_type() == "image/png"
          and parts["files[0]"].get_payload(decode=True) == b"\x89PNG-data"
          and parts["files[1]"].get_filename() == "notes.txt",
          list(parts),
        )
        check(
          "a reason goes to the audit log header, percent-encoded",
          call["headers"]["x-audit-log-reason"] == "because",
        )

        await api.update_message(5, 9, content="edited")
        call = seen[-1]
        check(
          "update_message: PATCH with only what you passed",
          call["method"] == "PATCH"
          and call["path"] == "/channels/5/messages/9"
          and json_of(call)["content"] == "edited"
          and "embeds" not in json_of(call),
          json_of(call),
        )
        gone = await api.delete_message(5, 9, reason="spam & ünïcode")
        call = seen[-1]
        check(
          "delete_message: DELETE, no body, None back, reason encoded",
          call["method"] == "DELETE"
          and call["path"] == "/channels/5/messages/9"
          and gone is None
          and call["headers"]["x-audit-log-reason"] == "spam%20%26%20%C3%BCn%C3%AFcode",
          call["headers"],
        )
        answers["GET /channels/5/messages"] = (200, [message])
        listed = await api.list_messages(5, limit=3, before=7)
        check(
          "list_messages: query parameters, a typed list back",
          seen[-1]["query"] == {"limit": "3", "before": "7"}
          and isinstance(listed, list)
          and len(listed) == 1,
          (seen[-1]["query"], type(listed)),
        )
        await api.bulk_set_application_commands(
          100, [{"name": "ping", "description": "p", "type": 1}]
        )
        body = json_of(seen[-1])
        check(
          "a list body is passed as `body`",
          seen[-1]["method"] == "PUT"
          and isinstance(body, list)
          and body[0]["name"] == "ping",
          body,
        )
        await api.update_channel(5, topic=None)
        check(
          "None is sent as null; what you leave out is not sent",
          json_of(seen[-1]) == {"topic": None},
          json_of(seen[-1]),
        )
        answers["POST /guilds/7/stickers"] = (
          200,
          {
            "id": "1",
            "name": "n",
            "tags": "t",
            "type": 2,
            "format_type": 1,
            "guild_id": "7",
            "available": True,
            "description": None,
          },
        )
        await api.create_guild_sticker(
          7,
          name="wave",
          tags="wave",
          description="d",
          file=Upload("wave.png", b"png", "image/png"),
        )
        call = seen[-1]
        envelope = message_from_bytes(
          b"Content-Type: "
          + call["headers"]["content-type"].encode()
          + b"\r\n\r\n"
          + call["body"],
          policy=email_policy,
        )
        parts = {
          part.get_param("name", header="content-disposition"): part
          for part in envelope.iter_parts()
        }
        check(
          "a multipart-only operation sends plain form fields and the file",
          parts["name"].get_content() == "wave"
          and "payload_json" not in parts
          and parts["file"].get_filename() == "wave.png",
          list(parts),
        )
        answers["PUT /guilds/7/bans/8"] = (
          403,
          {"code": 50013, "message": "Missing Permissions"},
        )
        try:
          await api.ban_user_from_guild(7, 8, delete_message_seconds=60, reason="r")
          caught = None
        except DiscordAPIError as error:
          caught = error
        check(
          "a Discord error raises DiscordAPIError with the status and body",
          caught is not None
          and caught.status == 403
          and isinstance(caught.body, dict)
          and caught.body["code"] == 50013,
          caught,
        )
        # Refs: an object by id, with its ids bound.
        from datetime import UTC
        from datetime import datetime as when

        await api.channel(5).send("via ref", embeds=[ui.embed("E")])
        check(
          "api.channel(5).send: POST to that channel",
          seen[-1]["method"] == "POST"
          and seen[-1]["path"] == "/channels/5/messages"
          and json_of(seen[-1])["content"] == "via ref",
        )
        await api.message(5, 9).reply("yo")
        check(
          "message.reply sets message_reference to the message",
          json_of(seen[-1])["message_reference"] == {"message_id": "9"}
          and seen[-1]["path"] == "/channels/5/messages",
          json_of(seen[-1]),
        )
        await api.message(5, 9).react("👍")
        check(
          "message.react: PUT .../reactions/<emoji>/@me",
          seen[-1]["method"] == "PUT"
          and seen[-1]["path"] == "/channels/5/messages/9/reactions/👍/@me",
          seen[-1]["path"],
        )
        await api.message(5, 9).react(ui.Emoji("wave", 123456))
        check(
          "a custom Emoji is written name:id in the path",
          seen[-1]["path"] == "/channels/5/messages/9/reactions/wave:123456/@me",
          seen[-1]["path"],
        )
        await api.member(7, 8).kick(reason="rule 1")
        check(
          "member.kick: DELETE with the audit reason",
          seen[-1]["method"] == "DELETE"
          and seen[-1]["path"] == "/guilds/7/members/8"
          and seen[-1]["headers"]["x-audit-log-reason"] == "rule%201",
        )
        await api.member(7, 8).add_role(20)
        check(
          "member.add_role: PUT .../roles/20",
          seen[-1]["method"] == "PUT"
          and seen[-1]["path"] == "/guilds/7/members/8/roles/20",
        )
        until = when(2030, 1, 2, 3, 4, 5, tzinfo=UTC)
        await api.member(7, 8).timeout(until, reason="cool off")
        check(
          "member.timeout: PATCH communication_disabled_until",
          seen[-1]["method"] == "PATCH"
          and json_of(seen[-1])["communication_disabled_until"].startswith(
            "2030-01-02T03:04:05"
          ),
          json_of(seen[-1]),
        )
        await api.member(7, 8).timeout(None)
        check(
          "member.timeout(None) lifts it with a real null",
          json_of(seen[-1]) == {"communication_disabled_until": None},
          json_of(seen[-1]),
        )
        answers.pop("PUT /guilds/7/bans/8", None)  # it answered 403 for the error check
        await api.guild(7).ban(8, delete_message_seconds=60, reason="r")
        check(
          "guild.ban: PUT /guilds/7/bans/8",
          seen[-1]["method"] == "PUT"
          and seen[-1]["path"] == "/guilds/7/bans/8"
          and json_of(seen[-1])["delete_message_seconds"] == 60,
          (seen[-1]["path"], json_of(seen[-1])),
        )
        check(
          "links carry ids: guild.member(8) is the same as api.member(7, 8)",
          api.guild(7).member(8) == api.member(7, 8)
          and api.channel(5).message(9) == api.message(5, 9),
        )
        answers["POST /users/@me/channels"] = (
          200,
          {"id": "55", "type": 1, "recipients": []},
        )
        await api.user(8).send("hello there")
        opened, sent_dm = seen[-2], seen[-1]
        check(
          "user.send opens the DM, then sends to it",
          opened["path"] == "/users/@me/channels"
          and json_of(opened) == {"recipient_id": "8"}
          and sent_dm["path"] == "/channels/55/messages",
          (opened["path"], sent_dm["path"]),
        )
        await api.webhook_token(3, "tok").execute(content="hook", wait=True)
        check(
          "webhook_token(...).execute: id and token in the path, query kept",
          seen[-1]["path"] == "/webhooks/3/tok"
          and seen[-1]["query"] == {"wait": "true"},
          (seen[-1]["path"], seen[-1]["query"]),
        )
        await api.channel(5).edit(topic=None, name="renamed")
        check(
          "channel.edit sends only what was given, nulls included",
          json_of(seen[-1]) == {"topic": None, "name": "renamed"},
          json_of(seen[-1]),
        )

        # Interaction shortcuts reach the same methods.
        payload = {
          "id": "1", "token": "tk", "application_id": "100", "type": 2, "guild_id": "7",
          "channel_id": "5", "data": {"name": "x"}, "member": {"user": {"id": "8", "username": "u"}, "roles": []},
          "message": {"id": "9", "channel_id": "5"},
        }  # fmt: skip
        from micro.discord.interactions import Interaction

        ctx = Interaction(payload, DiscordHTTPClient(runtime))
        await ctx.channel_ref.send("from ctx")
        await ctx.member_ref.add_role(30)
        await ctx.message_ref.pin()
        await ctx.guild_ref.unban(8)
        check(
          "ctx.channel_ref / member_ref / message_ref / guild_ref act on this interaction's objects",
          [c["path"] for c in seen[-4:]]
          == [
            "/channels/5/messages",
            "/guilds/7/members/8/roles/30",
            "/channels/5/pins/9",
            "/guilds/7/bans/8",
          ]
          or [c["path"] for c in seen[-4:]]
          == [
            "/channels/5/messages",
            "/guilds/7/members/8/roles/30",
            "/channels/5/messages/pins/9",
            "/guilds/7/bans/8",
          ],
          [c["path"] for c in seen[-4:]],
        )

        before = len(seen)
        try:
          await api.create_message(5, tts="maybe")  # type: ignore[arg-type]
          refused = False
        except ValidationError:
          refused = True
        check(
          "a bad argument fails before anything is sent",
          refused and len(seen) == before,
        )

        answers["GET /channels/5"] = (429, {"retry_after": 0.01, "global": False})
        try:
          await api.channel(5).get()  # retried until attempts run out
        except DiscordAPIError:
          pass
        limited = [e for e in hooked if e.rate_limited]
        check(
          "http hooks see every attempt with operation, status and duration",
          len(hooked) == len(seen)
          and len(limited) >= 2
          and [e.attempt for e in limited][:2] == [1, 2]
          and all(e.seconds >= 0 and e.operation and e.route for e in hooked)
          and hooked[0].status is not None,
          (len(hooked), len(seen)),
        )
        check(
          "a failing hook is logged and never breaks the request",
          len(late) == len(hooked) and len(late) > 0,
        )

        answers.pop("GET /channels/5")

        def force_reason(request: Any) -> Any:
          return request.model_copy(update={"reason": "rewritten"})

        undo = http_worker.rewrite(force_reason)
        await api.channel(5).get()
        check(
          "a rewriter changes the request before it is sent",
          seen[-1]["headers"].get("x-audit-log-reason") == "rewritten",
          seen[-1]["headers"],
        )

        def refuse(request: Any) -> None:
          if request.operation == "get_channel":
            raise ValueError("channels are off limits")

        undo_refuse = http_worker.rewrite(refuse)
        before = len(seen)
        try:
          await api.channel(5).get()
          refused = False
        except Exception as error:
          refused = "off limits" in str(error)
        check(
          "a rewriter can refuse a request; nothing is sent",
          refused and len(seen) == before,
          (refused, len(seen) - before),
        )
        undo()
        undo_refuse()
        unhook()
        count = len(late)
        await api.channel(5).get()
        check(
          "a removed hook stops being called",
          len(late) == count and len(hooked) > count,
        )
    finally:
      server.terminate()
      await server.wait()


async def scheduler_scenarios() -> None:
  print("scheduler: timers fire once, at their time, and survive a missing scheduler")
  from datetime import UTC, timedelta
  from datetime import datetime as when

  from pydantic import BaseModel

  from micro.queue import WorkQueue
  from micro.scheduler import Scheduler, Timers
  from micro.service import EventSchema

  class Note(BaseModel):
    text: str

  REMIND = EventSchema[Note](id="smoke.remind", payload=Note)
  CHORE = WorkQueue[Note]("smoke.chore", Note)
  arrivals: list[tuple[str, str, float]] = []
  started = time.monotonic()
  service = Service("sched-demo")

  @service.listen(REMIND)
  async def on_remind(note: Note) -> None:
    arrivals.append(("event", note.text, time.monotonic() - started))

  @service.work(CHORE)
  async def on_chore(note: Note) -> None:
    arrivals.append(("job", note.text, time.monotonic() - started))

  def got(kind: str, text: str) -> list[float]:
    return [at for k, t, at in arrivals if k == kind and t == text]

  async def waited(kind: str, text: str, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
      if got(kind, text):
        return True
      await asyncio.sleep(0.05)
    return False

  async with Stack(App()) as s:
    runtime = s.runtime
    await runtime.add(service)
    timers = Timers(runtime)
    scheduler = Scheduler()
    await runtime.add(scheduler)

    now = time.monotonic() - started
    await timers.event("t.event", REMIND, Note(text="soon"), after=1.5)
    await timers.job("t.job", CHORE, Note(text="chore"), after=2.0)
    check(
      "an event timer fires at its time",
      await waited("event", "soon", 6) and 1.0 <= got("event", "soon")[0] - now <= 3.5,
      got("event", "soon"),
    )
    check("a job timer reaches a worker", await waited("job", "chore", 6), arrivals)

    await timers.event("t.replace", REMIND, Note(text="first"), after=1.5)
    await timers.event("t.replace", REMIND, Note(text="second"), after=3.0)
    await asyncio.sleep(5)
    check(
      "scheduling a key again replaces it: only the new one fires",
      got("event", "first") == [] and len(got("event", "second")) == 1,
      arrivals,
    )

    await timers.event("t.cancel", REMIND, Note(text="never"), after=1.5)
    check("cancel removes a timer", await timers.cancel("t.cancel") is True)
    check(
      "cancel says when there was nothing", await timers.cancel("t.cancel") is False
    )
    await asyncio.sleep(3)
    check("a cancelled timer does not fire", got("event", "never") == [], arrivals)

    await timers.event(
      "t.past", REMIND, Note(text="late"), at=when.now(UTC) - timedelta(minutes=5)
    )
    check("a time in the past fires at once", await waited("event", "late", 3))

    # No scheduler running: timers wait, then are delivered when one starts.
    await scheduler.close()
    await timers.event("t.catchup", REMIND, Note(text="caught"), after=1.0)
    await asyncio.sleep(3)
    check(
      "with no scheduler, a due timer waits", got("event", "caught") == [], arrivals
    )
    pending = await timers.pending("t.")
    check(
      "pending is what is not yet due: a timer that came due is no longer listed",
      all(t.key != "t.catchup" for t in pending),
      pending,
    )
    replacement = Scheduler("scheduler")
    await runtime.add(replacement)
    check(
      "a new scheduler delivers what came due meanwhile",
      await waited("event", "caught", 4),
      arrivals,
    )

    # Two schedulers share the work: every timer is delivered exactly once.
    second = Scheduler("scheduler")
    await runtime.add(second)
    for n in range(8):
      await timers.event(f"t.many.{n}", REMIND, Note(text=f"m{n}"), after=1.0)
    await asyncio.sleep(4)
    counts = [len(got("event", f"m{n}")) for n in range(8)]
    check("two schedulers deliver each timer exactly once", counts == [1] * 8, counts)

    # Listing and lookup.
    soon = when.now(UTC) + timedelta(hours=1)
    later = when.now(UTC) + timedelta(hours=2)
    await timers.job("list.b", CHORE, Note(text="b"), at=later)
    await timers.event("list.a", REMIND, Note(text="a"), at=soon)
    listed = await timers.pending("list.")
    check(
      "pending: soonest first, with kind, target and payload",
      [t.key for t in listed] == ["list.a", "list.b"]
      and [t.kind for t in listed] == ["event", "job"]
      and [t.target for t in listed] == ["smoke.remind", "smoke.chore"]
      and listed[0].payload == {"text": "a"}
      and abs((listed[0].at - soon).total_seconds()) < 1,
      listed,
    )
    one = await timers.get("list.b")
    check(
      "get finds a timer, or None",
      one is not None and one.key == "list.b" and await timers.get("list.zzz") is None,
    )
    for key in ("list.a", "list.b"):
      await timers.cancel(key)


async def store_scenarios() -> None:
  print("store: the behavior docs/store.rst promises")
  from micro.store import GraphEngine, GraphModule, GraphQLBody, Store, StoreClient
  from micro.store.sqlite import SQLiteGraph

  commands = """
    type Guild @entity(key: ["id"]) {
      id: ID!
      name: String!
      prefix: String
      commands: [Command!]!
    }
    type Command @entity(key: ["guildId", "name"]) {
      guildId: ID!
      name: String!
      body: String!
      uses: Int!
      tags: [String!]!
      enabled: Boolean!
    }
    type Query {
      guild(id: ID!): Guild @from(key: {id: id})
      command(guildId: ID!, name: String!): Command @from(key: {guildId: guildId, name: name})
      allCommands(first: Int!, offset: Int!): [Command!]! @scan
    }
    type Mutation {
      addGuild(id: ID!, name: String!, prefix: String): Guild!
        @insert(key: {id: id}, set: {id: id, name: name, prefix: prefix})
      addCommand(guildId: ID!, name: String!, body: String!, tags: [String!] = []): Command!
        @insert(key: {guildId: guildId, name: name},
                set: {guildId: guildId, name: name, body: body, uses: "0", tags: tags, enabled: "TRUE"})
      attach(guildId: ID!, name: String!): Boolean
        @connect(fromType: "Guild", fromKey: {id: guildId}, toType: "Command",
                 toKey: {guildId: guildId, name: name}, field: "commands")
      detach(guildId: ID!, name: String!): Boolean
        @disconnect(fromType: "Guild", fromKey: {id: guildId}, toType: "Command",
                    toKey: {guildId: guildId, name: name}, field: "commands")
      editBody(guildId: ID!, name: String!, body: String): Command
        @update(key: {guildId: guildId, name: name}, set: {body: body})
      setEnabled(guildId: ID!, name: String!, enabled: Boolean!): Command
        @update(key: {guildId: guildId, name: name}, set: {enabled: enabled})
      bump(guildId: ID!, name: String!): Command
        @update(key: {guildId: guildId, name: name}, where: "current.enabled = TRUE",
                set: {uses: "current.uses + 1"})
      removeCommand(guildId: ID!, name: String!): Boolean
        @delete(type: "Command", key: {guildId: guildId, name: name})
    }
  """

  async def ask(
    engine: GraphEngine, query: str, variables: dict[str, Any] | None = None
  ) -> dict[str, Any]:
    return await engine.execute(GraphQLBody(query=query, variables=variables))  # type: ignore[arg-type]

  with tempfile.TemporaryDirectory() as raw:
    executor = SQLiteGraph(os.path.join(raw, "store.db"))
    await executor.start()
    engine = GraphEngine(executor)
    await engine.apply_modules([GraphModule(id="cmds", schema=commands)])
    check(
      "a module with every directive composes",
      engine.composition_error is None and engine.available,
    )

    made = await ask(
      engine, 'mutation { addGuild(id: "1", name: "Home") { id name prefix } }'
    )
    check(
      "an optional argument left out is unset (null), not an error",
      made["data"]["addGuild"] == {"id": "1", "name": "Home", "prefix": None},
      made,
    )
    dup = await ask(engine, 'mutation { addGuild(id: "1", name: "Again") { id } }')
    check(
      "inserting an existing key is a CONFLICT error",
      dup["data"] is None and dup["errors"][0]["extensions"]["code"] == "CONFLICT",
      dup,
    )
    added = await ask(
      engine,
      'mutation { addCommand(guildId: "1", name: "hello", body: "hi") { uses tags enabled } }',
    )
    check(
      "GQL literals and GraphQL argument defaults fill fields",
      added["data"]["addCommand"] == {"uses": 0, "tags": [], "enabled": True},
      added,
    )
    await ask(
      engine,
      'mutation { addCommand(guildId: "1", name: "bye", body: "bye", tags: ["x"]) { name } }',
    )
    await ask(
      engine,
      'mutation { a: attach(guildId: "1", name: "hello") b: attach(guildId: "1", name: "bye") }',
    )
    listing = await ask(engine, '{ guild(id: "1") { commands { name } } }')
    check(
      "a list-valued edge lists a guild's commands",
      sorted(c["name"] for c in listing["data"]["guild"]["commands"])
      == ["bye", "hello"],
      listing,
    )

    bumped = await ask(
      engine, 'mutation { bump(guildId: "1", name: "hello") { uses } }'
    )
    again = await ask(engine, 'mutation { bump(guildId: "1", name: "hello") { uses } }')
    check(
      "current.uses + 1 increments in place",
      (bumped["data"]["bump"], again["data"]["bump"]) == ({"uses": 1}, {"uses": 2}),
    )
    await ask(
      engine,
      'mutation { setEnabled(guildId: "1", name: "hello", enabled: false) { enabled } }',
    )
    blocked = await ask(
      engine, 'mutation { bump(guildId: "1", name: "hello") { uses } }'
    )
    check(
      "an update whose where is false changes nothing and returns null",
      blocked["data"]["bump"] is None,
      blocked,
    )

    await ask(
      engine, 'mutation { editBody(guildId: "1", name: "hello", body: "hey") { body } }'
    )
    left = await ask(
      engine, 'mutation { editBody(guildId: "1", name: "hello") { body uses } }'
    )
    check(
      "an update leaves out-of-request fields alone, including arguments not passed",
      left["data"]["editBody"] == {"body": "hey", "uses": 2},
      left,
    )
    cleared = await ask(
      engine, 'mutation { editBody(guildId: "1", name: "hello", body: null) { body } }'
    )
    check(
      "an explicit null clears a field",
      cleared["data"]["editBody"]["body"] is None,
      cleared,
    )
    missing = await ask(
      engine, 'mutation { editBody(guildId: "1", name: "nope", body: "x") { body } }'
    )
    check(
      "updating something that is not there returns null",
      missing["data"]["editBody"] is None,
      missing,
    )
    gone = await ask(engine, 'mutation { removeCommand(guildId: "1", name: "bye") }')
    after = await ask(engine, '{ guild(id: "1") { commands { name } } }')
    check(
      "delete removes the entity and its edges",
      gone["data"]["removeCommand"] is True
      and [c["name"] for c in after["data"]["guild"]["commands"]] == ["hello"],
      after,
    )
    await ask(engine, 'mutation { detach(guildId: "1", name: "hello") }')
    detached = await ask(engine, '{ guild(id: "1") { commands { name } } }')
    check(
      "disconnect removes just the edge",
      detached["data"]["guild"]["commands"] == [],
      detached,
    )

    atomic = await ask(
      engine,
      'mutation { ok: addCommand(guildId: "1", name: "atomic", body: "a") { name } '
      'bad: addCommand(guildId: "1", name: "atomic", body: "b") { name } }',
    )
    kept = await ask(engine, '{ command(guildId: "1", name: "atomic") { name } }')
    check(
      "the steps of one mutation request are all-or-nothing",
      atomic["data"] is None and kept["data"]["command"] is None,
      (atomic, kept),
    )

    for n in range(5):
      await ask(
        engine,
        f'mutation {{ addCommand(guildId: "2", name: "c{n}", body: "b") {{ name }} }}',
      )
    page = [
      [
        c["name"]
        for c in (
          await ask(engine, f'{{ allCommands(first: 2, offset: {o}) {{ name }} }}')
        )["data"]["allCommands"]
      ]
      for o in (0, 2, 4, 6)
    ]
    flat = [name for chunk in page for name in chunk]
    again = [
      [
        c["name"]
        for c in (
          await ask(engine, f"{{ allCommands(first: 2, offset: {o}) {{ name }} }}")
        )["data"]["allCommands"]
      ]
      for o in (0, 2, 4, 6)
    ]
    check(
      "scan pages cover every entity once, in a stable order that is not the key order",
      sorted(flat) == ["c0", "c1", "c2", "c3", "c4", "hello"]
      and page == again
      and flat != sorted(flat),
      (page, again),
    )
    wide = await ask(engine, '{ allCommands(first: 5000, offset: 0) { name } }')
    check(
      "scan allows at most 1000 per page",
      wide["data"] is None and "1000" in wide["errors"][0]["message"],
      wide,
    )

    # Evolving a schema: adding is safe, and removing only hides.
    v1 = 'type Note @entity(key: ["id"]) { id: ID! text: String! } type Query { note(id: ID!): Note @from(key: {id: id}) } type Mutation { addNote(id: ID!, text: String!): Note! @insert(key: {id: id}, set: {id: id, text: text}) }'
    v2 = 'type Note @entity(key: ["id"]) { id: ID! text: String! pinned: Boolean } type Query { note(id: ID!): Note @from(key: {id: id}) }'
    v3 = 'type Note @entity(key: ["id"]) { id: ID! } type Query { note(id: ID!): Note @from(key: {id: id}) }'
    await engine.apply_modules(
      [GraphModule(id="cmds", schema=commands), GraphModule(id="notes", schema=v1)]
    )
    await ask(engine, 'mutation { addNote(id: "1", text: "kept") { id } }')
    await engine.apply_modules(
      [GraphModule(id="cmds", schema=commands), GraphModule(id="notes", schema=v2)]
    )
    grown = await ask(engine, '{ note(id: "1") { text pinned } }')
    await engine.apply_modules(
      [GraphModule(id="cmds", schema=commands), GraphModule(id="notes", schema=v3)]
    )
    await engine.apply_modules(
      [GraphModule(id="cmds", schema=commands), GraphModule(id="notes", schema=v2)]
    )
    back = await ask(engine, '{ note(id: "1") { text } }')
    check(
      "a field added later reads null on old rows; one removed and restored keeps its data",
      grown["data"]["note"] == {"text": "kept", "pinned": None}
      and back["data"]["note"] == {"text": "kept"},
      (grown, back),
    )
    await executor.close()

  # The first module in docs/store.rst, taken from the page itself and run as written.
  import re

  page = (ROOT / "src/micro/docs/store.rst").read_text()
  documented = re.search(r'schema="""(.*?)"""', page, re.DOTALL)
  assert documented is not None
  with tempfile.TemporaryDirectory() as raw:
    executor = SQLiteGraph(os.path.join(raw, "docs.db"))
    await executor.start()
    engine = GraphEngine(executor)
    await engine.apply_modules(
      [GraphModule(id="myapp.commands", schema=documented.group(1))]
    )
    await ask(
      engine, 'mutation { addGuild(id: "1234", name: "Home", prefix: "!") { id } }'
    )
    flow = await ask(
      engine,
      'mutation($g: ID!, $n: String!, $b: String!) {'
      '  c: addCommand(guildId: $g, name: $n, body: $b) { name }'
      '  a: attach(guildId: $g, name: $n)'
      '}',
      {"g": "1234", "n": "hello", "b": "Hi!"},
    )
    used = await ask(
      engine, 'mutation { used(guildId: "1234", name: "hello") { uses } }'
    )
    shown = await ask(engine, '{ guild(id: "1234") { name commands { name uses } } }')
    check(
      "the module on the docs page composes and its flow works as written",
      engine.composition_error is None
      and flow["data"]["a"] is True
      and used["data"]["used"] == {"uses": 1}
      and shown["data"]["guild"]
      == {"name": "Home", "commands": [{"name": "hello", "uses": 1}]},
      (flow, used, shown),
    )
    await executor.close()

  # The documented flow: a service declares the module, a Store process serves it.
  async with Stack(App()) as stack:
    module = GraphModule(
      id="smoke.tags",
      schema="""
      type Tag @entity(key: ["name"]) { name: ID! uses: Int }
      type Query { tag(name: ID!): Tag @from(key: {name: name}) }
      type Mutation { addTag(name: ID!, uses: Int): Tag! @insert(key: {name: name}, set: {name: name, uses: uses}) }
    """,
    )
    owner = Service("tags")
    owner.uses(module)
    with tempfile.TemporaryDirectory() as raw:
      store = Store(SQLiteGraph(os.path.join(raw, "store.db")))
      await stack.runtime.add(store, owner)
      client = StoreClient(owner.client)
      deadline = time.monotonic() + 10
      result: dict[str, Any] = {}
      while time.monotonic() < deadline:
        try:
          result = await client.execute(
            'mutation { addTag(name: "py", uses: 3) { name uses } }'
          )
          if result.get("data"):
            break
        except Exception as error:  # the Store is still composing the module
          result = {"error": str(error)}
        await asyncio.sleep(0.2)
      check(
        "service.uses(module) + a Store process: StoreClient.execute works",
        (result.get("data") or {}).get("addTag") == {"name": "py", "uses": 3},
        result,
      )
      read = await client.execute(
        'query($n: ID!) { tag(name: $n) { uses } }', variables={"n": "py"}
      )
      check("variables work", read["data"]["tag"] == {"uses": 3}, read)


SCENARIOS: dict[str, Callable[[], Awaitable[None]]] = {
  "basics": basics,
  "sync": sync_scenarios,
  "runtime-commands": runtime_command_scenarios,
  "idle": idle_scenarios,
  "config": config_scenarios,
  "gateway-config": gateway_config_scenarios,
  "docs": docs_scenarios,
  "ui-hooks": ui_hooks_scenarios,
  "ui-limits": ui_limits_scenarios,
  "colour": colour_scenarios,
  "signed-ids": signed_ids_scenarios,
  "members": member_cache_scenarios,
  "endpoint": endpoint_scenarios,
  "custom": custom_package_scenarios,
  "cli": cli_scenarios,
  "pkg": pkg_scenarios,
  "service": service_scenarios,
  "routes": route_scenarios,
  "health": health_scenarios,
  "ui": ui_scenarios,
  "api": api_scenarios,
  "scheduler": scheduler_scenarios,
  "store": store_scenarios,
}


SCENARIO_TIMEOUT = 150
"""Seconds a scenario may take before it fails with a dump of what is waiting."""


async def main() -> int:
  wanted = sys.argv[1:]
  chosen = [n for n in SCENARIOS if not wanted or any(item in n for item in wanted)]
  if len(chosen) > 1 and not os.environ.get("SMOKE_CHILD"):
    return await main_parallel(chosen)
  timings: list[tuple[str, float]] = []
  for name in chosen:
    started = time.perf_counter()
    try:
      await asyncio.wait_for(SCENARIOS[name](), SCENARIO_TIMEOUT)
    except TimeoutError as error:
      print(
        f"  scenario {name} did not finish in {SCENARIO_TIMEOUT}s; it was waiting here:"
      )
      traceback.print_exception(error, limit=-8)
      check(f"scenario {name} finishes", False)
    timings.append((name, time.perf_counter() - started))
  failed = [name for name, ok in results if not ok]
  print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
  return len(failed)


async def main_parallel(chosen: list[str]) -> int:
  """Run each scenario in its own process, all at once.

  Scenarios own their NATS server, ports and fake Discord, so they do not interact;
  separate processes also keep the ones that edit the environment from leaking.
  """
  started = time.perf_counter()

  async def run(name: str) -> tuple[str, int, str, float]:
    begun = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
      sys.executable,
      __file__,
      name,
      env={**os.environ, "SMOKE_CHILD": "1"},
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return (
      name,
      proc.returncode or 0,
      out.decode(errors="replace"),
      time.perf_counter() - begun,
    )

  finished = await asyncio.gather(*(run(name) for name in chosen))
  passed = failed = 0
  for name, code, out, _ in finished:
    print(out, end="")
    for line in out.splitlines():
      if line.endswith(" failed") and " passed, " in line:
        counts = line.split()
        passed += int(counts[0])
        failed += int(counts[2])
    if code and not any(" passed, " in line for line in out.splitlines()):
      print(f"  FAIL  scenario {name} crashed (exit {code})")
      failed += 1
  print(f"\n{passed} passed, {failed} failed in {time.perf_counter() - started:.0f}s")
  print(
    "slowest:",
    ", ".join(
      f"{n} {t:.0f}s" for n, _, _, t in sorted(finished, key=lambda f: -f[3])[:5]
    ),
  )
  return failed


if __name__ == "__main__":
  sys.exit(asyncio.run(main()))
