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
from micro.discord import Context, DiscordHTTPClient, DiscordHTTPWorker, Message
from micro.discord.enums import ButtonStyle, ChannelType, TextInputStyle
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
from micro.discord.ui import Button, Draft, Modal, TextInput
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
    async def ping(ctx: Context, message: Message) -> None:
      api = DiscordHTTPClient(service.runtime).api
      (
        await api.channel(message.channel_id).send(Draft("pong", reply_to=message.id))
      ).unwrap()

    @commands.slash("hello", description="Say hello")
    async def hello(
      ctx: Context, interaction: Interaction, name: str = "world"
    ) -> None:
      await interaction.respond(
        Draft(
          f"Hello, {name}!",
          components=[Button("Wave back", custom_id=WAVE.encode(Wave(name=name)))],
        )
      )

    @components.match(WAVE)
    async def wave(ctx: Context, interaction: Interaction, state: Wave) -> None:
      await interaction.respond(
        Draft(f"{interaction.user.display_name} waves at {state.name}.", ephemeral=True)
      )

    @commands.slash("feedback", description="Open a modal")
    async def ask(ctx: Context, interaction: Interaction) -> None:
      await interaction.modal(
        Modal(
          FEEDBACK.encode(),
          "Feedback",
          [TextInput("text", "Thoughts", style=TextInputStyle.PARAGRAPH)],
        )
      )

    @modals.match(FEEDBACK)
    async def got(ctx: Context, interaction: Interaction) -> None:
      self.feedback.append(interaction.submitted.fields["text"])
      await interaction.respond(Draft("Thanks!", ephemeral=True))

    @commands.slash("slow", description="Defer, then answer")
    async def slow(ctx: Context, interaction: Interaction) -> None:
      await interaction.defer()
      await asyncio.sleep(0.2)
      await interaction.respond("done")

    self.dynamic = RuntimeCommands(service)

    @self.dynamic.handler
    async def custom(ctx: Context, interaction: Interaction) -> None:
      await interaction.respond(
        f"{interaction.command_name}@{interaction.guild_id} {interaction.submitted.options}"
      )

    if guild_commands:
      guilded = Commands(service, guild_ids=guild_commands)

      @guilded.slash("guilded", description="Only in some guilds")
      async def only(ctx: Context, interaction: Interaction) -> None:
        await interaction.respond("guilded")


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
    presence_ttl: float = 10.0,
  ) -> None:
    self.presence_ttl = presence_ttl
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
      f"nats://127.0.0.1:{port}",
      name="smoke",
      storage=StorageType.MEMORY,
      presence_ttl=self.presence_ttl,
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

      # The 5 s between identifies is Discord's rule; the fake Discord has none.
      await GatewayControl(self.runtime).configure(
        intents=int(intents), identify_interval=0.1
      )
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
      # Close without draining: a graceful drain (handing shards to a peer, waiting
      # out leases) is what the tests that are about draining check themselves.
      await self.runtime.close()
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


_BEGAN = time.monotonic()


def check(name: str, ok: bool, detail: object = "") -> None:
  results.append((name, ok))
  when = f"{time.monotonic() - _BEGAN:5.1f}s " if os.environ.get("SMOKE_TRACE") else ""
  print(
    f"  {when}{'PASS' if ok else 'FAIL'}  {name}"
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

    calls = await s.interact(f.slash("slow"), count=2)
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
      and await f.until(
        lambda: s.names("500") == [] and s.names("600") == ["greet"], 10
      ),
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


async def state_scenarios() -> None:
  print("state: each shard holds its guilds, and is asked")
  from micro.discord.permissions import Permissions
  from micro.discord.state import DiscordState
  from micro.gateway._state import ShardState

  def member(user_id: str, name: str, roles: list[str]) -> dict[str, Any]:
    return {
      "user": {"id": user_id, "username": name, "discriminator": "0", "avatar": None},
      "roles": roles,
      "joined_at": "2024-01-01T00:00:00+00:00",
      "deaf": False,
      "mute": False,
      "flags": 0,
    }

  def role(role_id: str, name: str, permissions: str = "0") -> dict[str, Any]:
    return {
      "id": role_id, "name": name, "permissions": permissions, "position": 1,
      "color": 0, "hoist": False, "managed": False, "mentionable": False,
    }  # fmt: skip

  def channel(
    channel_id: str, name: str, overwrites: list[Any] | None = None
  ) -> dict[str, Any]:
    return {
      "id": channel_id, "type": 0, "name": name,
      "permission_overwrites": overwrites or [],
    }  # fmt: skip

  intents = (
    hikari.Intents.ALL_UNPRIVILEGED
    | hikari.Intents.MESSAGE_CONTENT
    | hikari.Intents.GUILD_MEMBERS
  )
  fake_members = {
    "500": [member("1", "ann", ["10"]), member("2", "bob", ["11"])],
    "600": [member("1", "ann", ["20"])],
  }
  async with Stack(
    App(), guilds=("500", "600"), intents=intents, members=fake_members
  ) as s:
    f = s.fake
    await f.until(lambda: len(f.member_requests) >= 2, 15)
    state = DiscordState(s.runtime)

    async def held() -> bool:
      return await state.member(600, 1) is not None

    await eventually(held)
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
      "members are read from the shard that holds them, not REST",
      ann_500 is not None
      and ann_600 is not None
      and bob is not None
      and len(f.where("GET", r"/members/")) == rest,
    )
    check(
      "one user keeps a different member record in each guild",
      ann_500 is not None
      and ann_600 is not None
      and ann_500.roles == ["10"]
      and ann_600.roles == ["20"],
    )
    await f.dispatch(
      "GUILD_MEMBER_UPDATE", {"guild_id": "500", **member("2", "bob", ["11", "12"])}
    )
    await f.dispatch("GUILD_MEMBER_ADD", {"guild_id": "600", **member("3", "cy", [])})
    await eventually(
      lambda: state.member(500, 2), lambda m: m is not None and m.roles == ["11", "12"]
    )
    await eventually(lambda: state.member(600, 3), lambda m: m is not None)
    await state.member(500, 2)
    await state.user(1)
    await f.dispatch(
      "GUILD_MEMBER_UPDATE", {"guild_id": "600", **member("1", "ann-renamed", ["20"])}
    )
    await eventually(
      lambda: state.user(1),
      lambda u: u is not None and u.username == "ann-renamed",
    )
    check(
      "a user is the same in every guild: one change shows in all of them",
      (m := await state.member(500, 1)) is not None
      and m.user is not None
      and m.user.username == "ann-renamed",
    )

    # Many events carry a user, and each one keeps it current.
    def person(user_id: str, name: str) -> dict[str, Any]:
      return member(user_id, name, [])["user"]

    for event_name, payload, expected in (
      (
        "MESSAGE_CREATE",
        {"id": "7001", "guild_id": "500", "channel_id": "7", "content": "hi", "type": 0,
         "author": person("1", "via-message"), "timestamp": "2024-01-01T00:00:00+00:00"},
        "via-message",
      ),
      (
        "PRESENCE_UPDATE",
        {"user": {"id": "1", "username": "via-presence"}, "guild_id": "500",
         "status": "online", "activities": [], "client_status": {}},
        "via-presence",
      ),
      (
        "VOICE_STATE_UPDATE",
        {"guild_id": "500", "user_id": "1", "channel_id": None, "session_id": "x",
         "deaf": False, "mute": False, "self_deaf": False, "self_mute": False,
         "suppress": False, "member": member("1", "via-voice", [])},
        "via-voice",
      ),
      ("USER_UPDATE", person("1", "via-user-update"), "via-user-update"),
    ):  # fmt: skip
      await f.dispatch(event_name, payload)
      seen = await eventually(
        lambda: state.user(1),
        lambda u, want=expected: u is not None and u.username == want,
      )
      check(
        f"{event_name} keeps the user current",
        seen is not None and seen.username == expected,
      )
    await f.dispatch(
      "GUILD_BAN_ADD", {"guild_id": "500", "user": person("9", "banned")}
    )
    await eventually(lambda: state.user(9), lambda u: u is not None)
    await f.dispatch(
      "PRESENCE_UPDATE", {"user": {"id": "777"}, "guild_id": "500", "status": "idle",
                          "activities": [], "client_status": {}}
    )  # fmt: skip
    await f.dispatch(
      "GUILD_ROLE_CREATE", {"guild_id": "500", "role": role("95", "after-presence")}
    )
    await eventually(lambda: state.role(95), lambda r: r is not None)
    await f.dispatch(
      "GUILD_MEMBER_REMOVE", {"guild_id": "500", "user": member("2", "bob", [])["user"]}
    )
    await eventually(lambda: state.member(500, 2), lambda m: m is None)
    check(
      "a member who left is gone, and only from that guild",
      await state.member(500, 2) is None and await state.member(600, 1) is not None,
    )

    # Roles and channels: by guild or by id, and always current.
    everyone = role("500", "@everyone", str(int(Permissions.VIEW_CHANNEL)))
    mods = role("90", "mods", str(int(Permissions.MANAGE_MESSAGES)))
    await f.dispatch(
      "GUILD_CREATE",
      {
        "id": "500", "name": "five", "owner_id": "99", "unavailable": False,
        "roles": [everyone, mods],
        "channels": [channel("7", "general"), channel("8", "staff")],
        "members": [member("1", "ann", ["90"])],
      },
    )  # fmt: skip
    await eventually(lambda: state.roles(500), lambda r: r is not None and len(r) == 2)
    roles = await state.roles(500)
    channels = await state.channels(500)
    check(
      "roles and channels are listed by guild",
      roles is not None
      and sorted(r.id for r in roles) == ["500", "90"]
      and channels is not None
      and sorted(c.id for c in channels) == ["7", "8"],
      (roles, channels),
    )
    found_role = await state.role(90)
    found_channel = await state.channel(8)
    check(
      "and by id alone, without saying which guild",
      found_role is not None
      and found_role.name == "mods"
      and found_channel is not None
      and found_channel.guild_id == "500"
      and found_channel.name == "staff",
    )
    await f.dispatch(
      "GUILD_ROLE_UPDATE",
      {
        "guild_id": "500",
        "role": role("90", "moderators", str(int(Permissions.MANAGE_MESSAGES))),
      },
    )
    await f.dispatch(
      "GUILD_ROLE_CREATE", {"guild_id": "500", "role": role("91", "vip")}
    )
    await f.dispatch("CHANNEL_UPDATE", {"guild_id": "500", **channel("7", "lobby")})
    await f.dispatch("GUILD_ROLE_DELETE", {"guild_id": "500", "role_id": "999"})
    await eventually(
      lambda: state.roles(500),
      lambda r: (
        r is not None
        and len(r) == 3
        and {x.id: x.name for x in r}["90"] == "moderators"
      ),
    )
    await eventually(
      lambda: state.channel(7), lambda c: c is not None and c.name == "lobby"
    )
    roles = await state.roles(500)
    check(
      "a role edit is seen at once, in the list and by id (it was stale before)",
      roles is not None
      and sorted(r.id for r in roles) == ["500", "90", "91"]
      and {r.id: r.name for r in roles}["90"] == "moderators"
      and (await state.role(91)) is not None
      and (await state.channel(7)).name == "lobby",  # type: ignore[union-attr]
      roles,
    )
    await f.dispatch("GUILD_ROLE_DELETE", {"guild_id": "500", "role_id": "91"})
    await f.dispatch("CHANNEL_DELETE", {"guild_id": "500", **channel("8", "staff")})
    await eventually(lambda: state.role(91), lambda r: r is None)
    await eventually(lambda: state.channel(8), lambda c: c is None)
    check(
      "a deleted role or channel is gone from the list and from lookup by id",
      await state.role(91) is None
      and await state.channel(8) is None
      and sorted(c.id for c in (await state.channels(500)) or []) == ["7"],
    )
    allowed = await state.permissions(500, 1, 7)
    check(
      "permissions come from the same aggregate",
      allowed is not None
      and allowed.allows(Permissions.MANAGE_MESSAGES)
      and not allowed.allows(Permissions.BAN_MEMBERS),
      allowed,
    )
    await f.dispatch("GUILD_MEMBER_ADD", {"guild_id": "500", **member("3", "cy", [])})
    await eventually(lambda: state.member(500, 3), lambda m: m is not None)
    requests = len(f.member_requests)
    await f.dispatch("GUILD_DELETE", {"id": "500", "unavailable": True})
    await eventually(lambda: state.role(90), lambda r: r is None)
    check(
      "a guild in an outage is kept but not current: it holds nothing until it is back",
      await state.role(90) is None and await state.member(500, 1) is None,
    )
    await f.dispatch(
      "GUILD_CREATE",
      {"id": "500", "name": "five", "owner_id": "99", "unavailable": False,
       "roles": [everyone], "channels": [channel("7", "lobby")], "members": []},
    )  # fmt: skip
    await f.until(lambda: len(f.member_requests) > requests, 10)
    await eventually(  # the list arrives (one batch: its members and the clean-up)
      lambda: state.member(500, 1), lambda m: m is not None and m.roles == ["10"]
    )
    refilled = await state.member(500, 1)
    check(
      "a GUILD_CREATE replaces roles and channels at once, and asks for the member list again",
      await state.role(90) is None
      and [r.id for r in (await state.roles(500)) or []] == ["500"]
      and len(f.member_requests) > requests,
    )
    check(
      "members are kept until the list arrives, then those it does not list are removed",
      refilled is not None
      and refilled.roles == ["10"]
      and await state.member(500, 2) is not None
      and await state.member(500, 3) is None,
      (refilled, await state.member(500, 3)),
    )
    await f.dispatch(
      "MESSAGE_CREATE",
      {"id": "4242", "guild_id": "500", "channel_id": "7", "content": "hi", "type": 0,
       "author": member("1", "ann", [])["user"], "timestamp": "2024-01-01T00:00:00+00:00"},
    )  # fmt: skip
    # Roles are state: once this one shows, the message before it has been folded in.
    await f.dispatch(
      "GUILD_ROLE_CREATE", {"guild_id": "500", "role": role("93", "next")}
    )
    await eventually(lambda: state.role(93), lambda r: r is not None)
    # Messages are events, not state: a shard does not keep them.
    check(
      "events that are not state (messages) are not kept",
      state_unit_ignores_messages(ShardState),
    )

    # A user is global; its guilds are what the shards know, and each leads to the member.
    me = await state.me()
    check(
      "the bot's own user comes from READY, and guilds lists every guild held",
      me is not None
      and me.id == "100"
      and sorted(g.id for g in await state.guilds()) == ["500", "600"],
      (me, await state.guilds()),
    )
    from micro.discord import Context, DiscordHTTPClient

    context = Context(DiscordHTTPClient(s.runtime), application_id="100")
    try:
      repr(context.client)
      refused_client = False
    except RuntimeError:
      refused_client = True
    check(
      "a context reaches the Gateway, the timers, the store and the state; a client needs a service",
      type(context.gateway).__name__ == "GatewayControl"
      and type(context.timers).__name__ == "Timers"
      and type(context.store).__name__ == "StoreClient"
      and context.state is context.state
      and context.application_id == "100"
      and refused_client,
    )
    bound = await context.state.member(600, 1)
    roster = await context.state.members(600)
    owning = await bound.get_guild() if bound is not None else None
    check(
      "objects read from state are bound: they navigate and carry every action",
      bound is not None
      and bound.context is context
      and callable(getattr(bound, "ban", None))
      and owning is not None
      and owning.id == "600"
      and "1" in {m.id for m in roster or []},
    )

    known = await state.mutual_guilds(1)
    members = [await g.member() for g in known]
    check(
      "mutual_guilds leads to the guilds a user is in, and each to its member",
      sorted(g.guild.id for g in known) == ["500", "600"]
      and all(
        m is not None and m.user is not None and m.user.id == "1" for m in members
      )
      and {m.roles[0] if m and m.roles else None for m in members} == {"10", "20"},
      (known, members),
    )
    check(
      "a user nothing has seen is unknown, not an error",
      await state.user(424242) is None
      and await state.member(500, 424242) is None
      and await state.member(31337, 1) is None,
    )


def state_unit_ignores_messages(shard_state: Any) -> bool:
  held = shard_state()
  held.apply("GUILD_CREATE", {"id": "5", "name": "g"}, chunks=False)
  held.apply(
    "MESSAGE_CREATE",
    {"id": "9", "guild_id": "5", "channel_id": "7", "content": "hi"},
    chunks=False,
  )
  return (
    held.answer("guild", {"guild_id": "5"}) is not None
    and held.answer("channel", {"id": "9"}) is None
  )


async def handover_scenarios() -> None:
  print("handover: a drained worker hands its shard over, and does not spin doing it")
  from micro.gateway import GatewayWorker

  passes = 0
  original = GatewayWorker._reconcile  # pyright: ignore[reportPrivateUsage]

  async def counted(self: GatewayWorker) -> None:
    nonlocal passes
    passes += 1
    await original(self)

  GatewayWorker._reconcile = counted  # type: ignore[method-assign]  # pyright: ignore[reportPrivateUsage]
  try:
    async with Stack(App(), extra_gateways=1) as s:
      workers = [
        c
        for c in s.runtime._components  # pyright: ignore[reportPrivateUsage]
        if isinstance(c, GatewayWorker)
      ]

      async def owners() -> list[GatewayWorker]:
        return [w for w in workers if w.publishing_shards]

      first = (await eventually(owners, bool))[0]
      other = next(w for w in workers if w is not first)
      before = passes
      await first.drain()
      await eventually(owners, lambda found: other in found)
      check(
        "the other worker publishes the shard once the first has drained",
        other.publishing_shards != () and not first.publishing_shards,
        (first.publishing_shards, other.publishing_shards),
      )
      check(
        "the drain waits for the handover instead of spinning",
        passes - before < 200,
        passes - before,
      )
  finally:
    GatewayWorker._reconcile = original  # type: ignore[method-assign]  # pyright: ignore[reportPrivateUsage]


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

    len(f.where("POST", r"/callback$"))
    reply = await post(f.slash("hello", [{"name": "name", "type": 3, "value": "bo"}]))
    body = reply.json()
    check(
      "the handler's first response is the HTTP reply",
      reply.status_code == 200
      and body["type"] == 4
      and "Hello, bo" in body["data"]["content"],
      reply.text,
    )
    await post(f.slash("feedback"))
    await post(f.component("nobody.handles:1"))
    endpoint = next(
      c for c in s.runtime.components if isinstance(c, InteractionEndpoint)
    )
    ignored = {**f.slash("hello"), "type": 99}  # routed nowhere, so never answered
    try:
      async with httpx2.AsyncClient() as client:
        raw = json.dumps(ignored).encode()
        await client.post(
          url,
          content=raw,
          headers={
            "x-signature-ed25519": private.sign(b"1700000000" + raw).hex(),
            "x-signature-timestamp": "1700000000",
          },
          timeout=0.5,
        )
      hung_up = False
    except httpx2.TimeoutException:
      hung_up = True
    released = await f.until(lambda: endpoint.in_flight == 0, 5)
    check(
      "when Discord hangs up on an unanswered interaction, the endpoint lets go",
      hung_up and released,
      (hung_up, endpoint.in_flight),
    )
    try:
      await asyncio.wait_for(
        InteractionEndpoint(public_key=public, port=port, name="second").start(
          s.runtime
        ),
        5,
      )
    except RuntimeError:
      pass
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


async def ui_limits_scenarios() -> None:
  print(
    "ui limits: counts accumulate as components are built; limits are checked on serialize"
  )
  from micro.discord import ui
  from micro.discord.ui import (
    ActionRow,
    Button,
    Container,
    Section,
    SelectOption,
    TextDisplay,
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
  section = Section(
    TextDisplay("a"),
    TextDisplay("bb"),
    TextDisplay("ccc"),
    accessory=Thumbnail("https://x/y.png"),
  )
  check(
    "a section counts its texts and accessory, and their text",
    section.components_count == 5 and section.text_count == 6,
  )
  check(
    "text is counted in UTF-16 units: an emoji is 2",
    ui.utf16_length("a😀") == 3 and TextDisplay("😀" * 2001).count == 4002,
  )
  ActionRow(button(1), button(2), button(3))
  ActionRow(ui.StringSelect("pick", [SelectOption("a"), SelectOption("b")]))
  check(
    "a select takes the whole row: slots 5",
    ui.StringSelect.slots == 5 and ui.UserSelect.slots == 5 and Button.slots == 1,
  )
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
    "a container over 40 in all fails on its own",
    "components in all is 42"
    in refused(lambda: Container(*[TextDisplay("t") for _ in range(41)]).to_dict()),
  )

  check(
    "eight (56), each fine alone, fail as a message",
    "components in all is 56"
    in refused(lambda: ui.message_body(components=[box() for _ in range(8)])),
  )
  [TextDisplay("x" * 1500) for _ in range(3)]
  with ui.hooks.scoped():
    ui.hooks.remove(ui.check_limits)
    check(
      "the check is middleware: remove it and it is off",
      ActionRow(*[button(i) for i in range(6)]).to_dict()["type"] == 1,
    )


async def helper_scenarios() -> None:
  print("helpers: permissions, error classes, text, picture links")
  from datetime import UTC, datetime

  from micro.discord import DiscordAPIError, DiscordServerError, NotFound
  from micro.discord.enums import ChannelType
  from micro.discord.http_service import DiscordHTTPResponse
  from micro.discord.objects import Channel, Guild, Member, Message, Role, User
  from micro.discord.permissions import Permissions
  from micro.discord.state import compute_permissions

  role = Role.model_validate({"id": "1", "permissions": "8200", "color": 5})
  check(
    "a role's permissions are named flags read from Discord's string",
    role.permissions == Permissions.ADMINISTRATOR | Permissions.MANAGE_MESSAGES
    and role.permissions.names == ["administrator", "manage_messages"],
    role.permissions,
  )
  member = Member.model_validate(
    {"guild_id": "9", "user": {"id": "5"}, "roles": ["1"], "permissions": "2"}
  )
  compute_permissions("9", None, [role], member, "5")

  def error(status: int, body: bytes = b"") -> DiscordAPIError:
    return DiscordAPIError(
      "op", DiscordHTTPResponse(status=status, headers=(), body=body)
    )

  gone = error(404, b'{"code": 10008, "message": "Unknown Message"}')
  check(
    "an error is raised as the class for its status, with Discord's code and message",
    isinstance(gone, NotFound)
    and gone.code == 10008
    and gone.message == "Unknown Message"
    and isinstance(error(503), DiscordServerError)
    and type(error(418)) is DiscordAPIError,
    type(gone),
  )
  datetime(2023, 11, 14, 22, 13, 20, tzinfo=UTC)
  check(
    "pictures are Assets: the default avatar without one, animated as gif, a server icon",
    User(id="80351110224678912").display_avatar.url.endswith("/embed/avatars/5.png")
    and User(id="80351110224678912").avatar is None
    and (animated := User(id="1", avatar="a_x").avatar) is not None  # type: ignore[arg-type]
    and animated.animated
    and animated.with_size(64).url.endswith("/avatars/1/a_x.gif?size=64")
    and animated.with_format("png").url.endswith("/avatars/1/a_x.png")
    and Guild(id="2").icon is None
    and str(Guild(id="2", icon="h").icon).endswith("/icons/2/h.png")  # type: ignore[arg-type]
    and User(id="1", avatar="h").model_dump(mode="json")["avatar"] == "h"  # type: ignore[arg-type]
    and Channel.model_validate({"id": "3", "type": 2}).type is ChannelType.GUILD_VOICE
    and Channel.model_validate({"id": "3", "type": 99}).type == 99,
  )

  def member_of(guild: str, user: str, **more: Any) -> Member:
    return Member.model_validate(
      {"guild_id": guild, "user": {"id": user, "username": "u"}, **more}
    )

  here = member_of("1", "2", avatar="h")
  check(
    "a member is its guild and its user: equal when both are, with its own picture",
    here == member_of("1", "2", nick="other")
    and here != member_of("9", "2")
    and here != member_of("1", "3")
    and len({here, member_of("1", "2")}) == 1
    and here.guild_id == "1"
    and here.id == "2"
    and here.avatar is not None
    and here.avatar.url.endswith("/guilds/1/users/2/avatars/h.png")
    and member_of("1", "2").display_avatar == member_of("1", "2").user.display_avatar
    and here.model_dump(mode="json")["avatar"] == "h",
  )
  try:
    Member.model_validate({"user": {"id": "2"}})
    refused_member = False
  except ValueError:
    refused_member = True
  check("a member without its guild is refused", refused_member)

  from types import SimpleNamespace

  from micro.discord import Context
  from micro.discord.interactions._commands import parse_options
  from micro.discord.interactions._inject import call

  async def both(ctx: Context, interaction: Interaction, size: int = 1) -> Any:
    return (ctx, interaction, size)

  async def only(ctx: Context, interaction: Interaction) -> Any:
    return interaction

  from micro.service._inject import call_handler

  class FakeService:
    runtime = SimpleNamespace()

  async def on_message(ctx: Context, message: Message) -> Any:
    return ctx, message

  service = FakeService()
  from micro import subjects

  earlier = SimpleNamespace(
    headers={subjects.BEFORE_HEADER: '{"id":"9","channel_id":"5","content":"old"}'}
  )
  got_ctx, got_message = await call_handler(
    service,
    on_message,
    Message.model_validate({"id": "9", "channel_id": "5", "content": "hi"}),
    earlier,
  )
  check(
    "an event handler gets the context and the payload bound to it, with .before",
    isinstance(got_ctx, Context)
    and got_message.id == "9"
    and got_message.context is got_ctx
    and got_message.before is not None
    and got_message.before.content == "old"
    and got_message.before.context is got_ctx
    and (await call_handler(service, on_message, Message(id="9", channel_id="5")))[
      1
    ].before
    is None,
  )

  from micro.discord import Role

  made = Role.model_validate({"guild_id": "5", "role": {"id": "9", "name": "mods"}})
  gone = Role.model_validate({"guild_id": "5", "role_id": "9"})

  async def role_changed(ctx: Context, role: Role) -> Any:
    return role

  seen = await call_handler(
    service,
    role_changed,
    made,
    SimpleNamespace(headers={"Micro-Before": '{"id":"9","name":"old"}'}),
  )
  check(
    "role events are a Role with its guild, and .before knows the guild too",
    (made.id, made.guild_id, made.name) == ("9", "5", "mods")
    and (gone.id, gone.guild_id) == ("9", "5")
    and seen.before is not None
    and seen.before.name == "old"
    and seen.before.guild_id == "5",
  )

  import threading
  from http.server import BaseHTTPRequestHandler, HTTPServer

  from micro.discord import DownloadError, Err, download

  class Files(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
      found = self.path == "/a.png"
      self.send_response(200 if found else 404)
      self.end_headers()
      self.wfile.write(b"png-bytes" if found else b"")

    def log_message(self, format: str, *args: Any) -> None:
      pass

  files = HTTPServer(("127.0.0.1", 0), Files)
  threading.Thread(target=files.serve_forever, daemon=True).start()
  base = f"http://127.0.0.1:{files.server_port}"
  found_file = await download(f"{base}/a.png")
  missing_file = await download(f"{base}/gone.png")
  files.shutdown()
  files.server_close()
  unreachable = await download(f"{base}/a.png")
  check(
    "download returns the bytes, or an Err with the status or the connection failure",
    found_file.unwrap() == b"png-bytes"
    and (missing_file.unwrap_or(None) is None)
    and unreachable.is_err,
  )
  check(
    "a missing file carries its HTTP status",
    isinstance(missing_file, Err)
    and isinstance(missing_file.error, DownloadError)
    and missing_file.error.status == 404,
  )

  import inspect

  from micro.discord import objects as object_module
  from micro.discord import refs as ref_module

  absent: list[str] = []
  for view_name, ref_name in (
    ("Message", "MessageRef"),
    ("Member", "MemberRef"),
    ("User", "UserRef"),
    ("Channel", "ChannelRef"),
    ("Guild", "GuildRef"),
    ("Role", "RoleRef"),
  ):
    view = getattr(object_module, view_name)
    for method, _ in inspect.getmembers(
      getattr(ref_module, ref_name), inspect.isfunction
    ):
      if method.startswith("_"):
        continue
      name = "fetch" if method == "get" else method
      if not (hasattr(view, name) or hasattr(view, f"fetch_{name}")):
        absent.append(f"{view_name}.{method}")
  check(
    "every action of every ref is on its object (no road without a path)",
    not absent,
    absent,
  )

  import json

  from micro.gateway._state import ShardState
  from micro.subjects import BEFORE_HEADER

  def event_data(**data: Any) -> Any:
    return data

  held_state = ShardState()
  held_state.apply("GUILD_CREATE", event_data(id="5", name="g"), chunks=False)
  person = {"id": "1", "username": "a"}
  held_state.apply(
    "GUILD_MEMBER_ADD",
    event_data(guild_id="5", user=person, roles=[]),
    chunks=False,
  )
  earlier = held_state.apply(
    "GUILD_MEMBER_UPDATE",
    event_data(guild_id="5", user=person, roles=["9"]),
    chunks=False,
  )
  removed = held_state.apply(
    "GUILD_MEMBER_REMOVE", event_data(guild_id="5", user=person), chunks=False
  )

  async def changed(ctx: Context, member: Member) -> Any:
    return member.before, member

  pair = await call_handler(
    service,
    changed,
    Member.model_validate({"guild_id": "5", "user": person, "roles": ["9"]}),
    SimpleNamespace(headers={BEFORE_HEADER: json.dumps(earlier)}),
  )
  first = await call_handler(
    service,
    changed,
    Member.model_validate({"guild_id": "5", "user": person, "roles": []}),
    SimpleNamespace(headers={}),
  )
  check(
    "an update event carries the object as it was, as event.before",
    earlier is not None
    and earlier["roles"] == []
    and removed is not None
    and removed["roles"] == ["9"]
    and pair[0] is not None
    and pair[0].roles == []
    and pair[1].roles == ["9"]
    and pair[0].context is pair[1].context
    and first[0] is None,
    (earlier, removed, pair, first),
  )

  fake = SimpleNamespace(context="the context")
  check(
    "every interaction handler is called with the context, the interaction, then its options",
    await call(both, fake, 5) == ("the context", fake, 5)
    and await call(only, fake) is fake
    and [o.name for o in parse_options(both)] == ["size"]
    and parse_options(only) == [],
  )
  Message.model_validate(
    {"id": "9", "channel_id": "5", "guild_id": "2", "attachments": [{"id": "7"}]}
  )


def _raises(action: Any, kind: type[Exception] = ValueError) -> str:
  try:
    action()
  except kind as error:
    return str(error) or kind.__name__
  return ""


async def logging_scenarios() -> None:
  print("logging: fields, call path, and error results nobody looked at")
  import gc
  import logging

  from micro import log
  from micro._handling import handling
  from micro.result import Err, UnhandledResult
  from micro.result import handling as watching

  class Catch(logging.Handler):
    def __init__(self) -> None:
      super().__init__(logging.DEBUG)
      self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
      self.records.append(record)

  catch = Catch()
  root = logging.getLogger()
  previous = root.level
  root.addHandler(catch)
  root.setLevel(logging.DEBUG)
  try:
    log.info("sent report", guild=1, name="two words")
    record = catch.records[-1]
    check(
      "a line shows its fields, and keeps them on the record",
      record.getMessage() == "sent report  guild=1 name='two words'"
      and record.fields == {"guild": 1, "name": "two words"}  # type: ignore[attr-defined]
      and record.path == (),  # type: ignore[attr-defined]
      record.getMessage(),
    )
    check(
      "the logger is named for the calling module, and the line points at the caller",
      record.name == __name__ and record.funcName == "logging_scenarios",
      (record.name, record.funcName),
    )
    log.warning("retry in %.1fs", 0.5, route="x")
    log.info("100% sure", note="50%")

    with log.context(interaction=77), log.step("outer"):

      async def inner() -> None:
        with log.step("inner"):
          log.error("deep", error=ValueError("x"))

      await asyncio.create_task(inner())
      log.bind(user=3).info("bound")
    deep = next(r for r in catch.records if r.getMessage().startswith("deep"))
    next(r for r in catch.records if r.getMessage().startswith("bound"))
    check(
      "the call path and context fields follow the work into a task it starts",
      "path=outer > inner  interaction=77 error=ValueError('x')" in deep.getMessage()
      and deep.path == ("outer", "inner"),  # type: ignore[attr-defined]
      deep.getMessage(),
    )

    @log.step("decorated")
    async def decorated() -> None:
      log.info("in decorated")

    await decorated()
    try:
      with log.step("risky"):
        raise KeyError("boom")
    except KeyError:
      log.exception("it failed")
    check(
      "a step that raises says so, and exception() carries the traceback",
      any(r.getMessage().startswith("risky failed in") for r in catch.records)
      and catch.records[-1].exc_info is not None,
    )

    # Error results nobody looked at.
    def made() -> Err[ValueError]:
      return Err(ValueError("lost"))

    def trips(body: Any) -> str:
      try:
        with watching():
          body()
      except UnhandledResult as error:
        return str(error)
      return ""

    check(
      "a handler that drops an Err fails, naming the error and where it was made",
      "lost" in trips(made) and "made" in trips(made) and "smoke.py" in trips(made),
      trips(made),
    )

    def matched() -> None:
      match made():
        case Err(ValueError() as error):
          assert str(error) == "lost"

    def raised() -> None:
      made()
      raise RuntimeError("the real failure")

    try:
      with watching():
        raised()
      kept = None
    except RuntimeError as error:
      kept = str(error)
    check("a handler that raised keeps its own error", kept == "the real failure")

    async def spawned() -> str:
      try:
        with watching():

          async def child() -> None:
            made()

          await asyncio.create_task(child())
      except UnhandledResult as error:
        return str(error)
      return ""

    check(
      "an Err made in a task the handler started counts too",
      "lost" in await spawned(),
    )

    before = len(catch.records)
    made()
    gc.collect()
    dropped = [
      r
      for r in catch.records[before:]
      if "dropped without being looked at" in r.getMessage()
    ]
    check(
      "outside a handler a dropped Err is logged when it is collected",
      len(dropped) == 1
      and dropped[0].levelno == logging.ERROR
      and "lost" in dropped[0].getMessage(),
      [r.getMessage() for r in catch.records[before:]],
    )
    before = len(catch.records)
    made().unwrap_or(None)
    gc.collect()

    try:
      with handling("svc", "event x", interaction=5):
        log.info("inside")
        made()
    except UnhandledResult:
      pass
    inside = next(r for r in catch.records if r.getMessage().startswith("inside"))
    check(
      "Micro's handler wrapper sets the path and fields for everything inside",
      "path=svc > event x" in inside.getMessage()
      and "interaction=5" in inside.getMessage(),
      inside.getMessage(),
    )
  finally:
    root.removeHandler(catch)
    root.setLevel(previous)


async def error_hook_scenarios() -> None:
  print("error hook: what an interaction does when its handler raised")
  from micro.discord.interactions import (
    Commands,
    Flow,
    InteractionRouter,
    report_failure,
  )
  from micro.discord.ui import Draft
  from micro.result import Err

  class Recorder:
    """Stands in for the HTTP client: records the interaction responses sent."""

    def __init__(self) -> None:
      self.sent: list[Any] = []

    async def call(self, operation: str, **parts: Any) -> Any:
      self.sent.append((operation, parts.get("body")))

  def flow_for(recorder: Recorder, number: int) -> Flow:
    payload = {
      "id": str(1000000000000000 + number), "token": f"t{number}",
      "application_id": "100", "type": 2, "data": {"name": "x"}, "user": {"id": "1"},
    }  # fmt: skip
    return Flow(payload, http=recorder, key="x")  # type: ignore[arg-type]

  async def run(commands: Commands, number: int) -> Recorder:
    recorder = Recorder()
    await commands.handle(flow_for(recorder, number))
    return recorder

  def boom(commands: Commands) -> None:
    @commands.use
    async def fails(flow: Flow, next: Any) -> None:
      raise RuntimeError("boom")

  default = Commands(Service("errors.default"))
  boom(default)
  recorder = await run(default, 1)
  body = recorder.sent[0][1]["data"] if recorder.sent else {}
  check(
    "by default the user gets an ephemeral 'Something went wrong.'",
    len(recorder.sent) == 1
    and body.get("content") == "Something went wrong."
    and body.get("flags") == 64,
    recorder.sent,
  )

  dropping = Commands(Service("errors.dropping"))

  @dropping.use
  async def drops(flow: Flow, next: Any) -> None:
    Err(ValueError("lost"))
    await next()

  recorder = await run(dropping, 2)
  check(
    "an error result nobody looked at goes the same way",
    len(recorder.sent) == 1
    and recorder.sent[0][1]["data"]["content"] == "Something went wrong.",
    recorder.sent,
  )

  seen: list[BaseException] = []
  custom = Commands(Service("errors.custom"))
  boom(custom)

  @custom.on_error
  async def failed(flow: Flow, error: BaseException) -> None:
    seen.append(error)
    await flow.interaction.respond(Draft(f"Custom: {error}", ephemeral=True))

  recorder = await run(custom, 3)
  check(
    "an error hook replaces the default, and gets the flow and the error",
    len(recorder.sent) == 1
    and recorder.sent[0][1]["data"]["content"] == "Custom: boom"
    and len(seen) == 1
    and isinstance(seen[0], RuntimeError),
    recorder.sent,
  )

  quiet = Commands(Service("errors.quiet"))
  boom(quiet)

  @quiet.on_error
  async def say_nothing(flow: Flow, error: BaseException) -> None:
    return None

  check("a hook that does nothing sends nothing", (await run(quiet, 4)).sent == [])

  broken = Commands(Service("errors.broken"))
  boom(broken)

  @broken.on_error
  async def also_fails(flow: Flow, error: BaseException) -> None:
    raise KeyError("the hook itself broke")

  check(
    "a hook that raises is logged and does not escape",
    (await run(broken, 5)).sent == [],
  )

  mine = InteractionRouter()
  check(
    "the router has one too, and the default is exported to build on",
    mine.on_error(say_nothing) is say_nothing and callable(report_failure),
  )


async def config_scenarios() -> None:
  print("config: typed, shared, revision-safe settings with refresh middleware")
  from pydantic import BaseModel, ConfigDict

  import micro.config as config_module

  # The real backoff (1 s, 2 s, 4 s, ...) is what protects a deployment; a test of the
  # retrying only needs the retries to happen, so it runs on a much shorter one.
  config_module.default_backoff = lambda attempt: 0.2 * attempt

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
      await one.update(rate=30)
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

      # Latest wins while deferred
      hold["on"] = True
      await two.update(rate=77, name="x")
      latest = await two.update(rate=78)
      await one.wait_for(latest.revision, timeout=5)

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
      await press("esc", "up", "enter", "down", "enter")  # gateway, then its intents
      await typed("unprivileged,message_content")
      await press("enter")
      await stored("gateway")
      await press("down", "down", "down", "enter")  # lease_ttl
      await typed("1")
      await press("enter")
      check(
        "a value the model refuses is shown and not written",
        app.message[0] == "error" and (await stored("gateway"))["lease_ttl"] == 10.0,
        app.message,
      )
      await press("up", "up", "up", "enter", "esc")
      await ctable.put("limits", {"rate": 5, "pool": 4})
      follower = asyncio.create_task(app.follow())
      await asyncio.sleep(0.3)
      await ctable.put("limits", {"rate": 6, "pool": 4})
      await asyncio.sleep(0.5)
      follower.cancel()

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
    finally:
      server.terminate()
      await server.wait()


async def gateway_config_scenarios() -> None:
  print("gateway intents and settings: one way to set intents")
  import hikari

  from micro.gateway import GatewayControl

  GatewayWorker(TOKEN)
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
    await control.status()
    await control.set_intents(int(new))
    try:
      await control.set_intents("nonsense")
    except ValueError:
      pass
    await control.set_shard_count(1)

    await control.configure(max_concurrency=2, lease_ttl=6.0)
    await _until_async(
      lambda: asyncio.sleep(0, [w.max_concurrency for w in workers]),
      lambda values: values == [2, 2],
      10,
    )
    config = await control.settings()
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
    await config.read()


async def eventually(read: Any, ok: Any = bool, timeout: float = 15) -> Any:
  """Poll an async reader until `ok(value)`, and return the value (the tests wait for
  what they expect to happen, not for a time to pass)."""
  deadline = time.monotonic() + timeout
  value = await read()
  while not ok(value) and time.monotonic() < deadline:
    await asyncio.sleep(0.02)
    value = await read()
  return value


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
    await asyncio.sleep(0.5)  # let the start-up churn settle
    counts = {w.name: 0 for w in workers}
    for worker in workers:
      original = worker._reconcile  # pyright: ignore[reportPrivateUsage]

      async def counted(original: Any = original, name: str = worker.name) -> None:
        counts[name] += 1
        await original()

      worker._reconcile = counted  # type: ignore[method-assign]  # pyright: ignore[reportPrivateUsage]
    await asyncio.sleep(1.5)
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
    f.rate_limit(r"/applications/\d+/commands$", retry_after=0.1, times=2)
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

  async with Stack(App(), presence_ttl=3) as s:
    from micro.discord.interactions import SYNC_LOCK, sync_commands

    async def consumers() -> int:
      return (await s.runtime.jetstream.account_info()).consumers

    settled = await consumers()
    for _ in range(100):  # startup creates consumers: wait until the count holds still
      await asyncio.sleep(0.15)
      now = await consumers()
      if now == settled:
        break
      settled = now
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
    await asyncio.sleep(
      2.5
    )  # presence refreshes (every second here); an idle CommandSync must not poll
    check(
      "an idle deployment does not accumulate consumers",
      (idle := await consumers()) == before,
      (before, idle),
    )


async def cli_dev_scenarios() -> None:
  await cli_scenarios(dev=True)


async def cli_scenarios(dev: bool = False) -> None:
  print(
    "cli: `micro dev`"
    if dev
    else "cli: the server and the nodes, as separate processes"
  )
  from micro.launch import reachable

  bin_dir = ROOT / ".venv/bin"
  env = os.environ | {"PATH": f"{bin_dir}:{os.environ['PATH']}"}
  micro = [sys.executable, "-m", "micro"]
  procs: list[Any] = []

  def project(directory: Path, port: int) -> None:
    (directory / "micro.toml").write_text(
      f'name = "demo"\nnats = "nats://127.0.0.1:{port}"\n'
      '[processes.app]\ncomponents = ["services.*"]\nreplicas = 1\n'
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

  async def cli_report(directory: Path) -> dict[str, Any]:
    """What `micro nodes list --json` prints (a process of its own each time)."""
    code, out = await cli(directory, "nodes", "list", "--json", merge=False)
    return (
      json.loads(out) if code == 0 and out.strip() else {"nodes": {}, "components": []}
    )

  watching: dict[int, Runtime] = {}

  async def report(directory: Path) -> dict[str, Any]:
    """The same report, read over one connection kept open: the tests poll it, and a
    process per poll would be most of what they cost."""
    from micro.launch import NODE_KIND

    if port not in watching:
      if not await reachable("127.0.0.1", port):
        return {"nodes": {}, "components": []}
      try:
        runtime = Runtime(f"nats://127.0.0.1:{port}", name="watch")
        await runtime.start()
        watching[port] = runtime
      except Exception:
        return {"nodes": {}, "components": []}
    runtime = watching[port]
    nodes = {
      e.name: e
      for e in runtime.directory.entries(NODE_KIND)
      if e.metadata.get("deployment") == "demo"
    }
    found: dict[str, Any] = {"nodes": {}, "components": []}
    for node in sorted(nodes):
      try:
        reply = await runtime.nats.request(
          subjects.node("demo", node, "ps"), b"{}", timeout=5
        )
      except Exception:
        reply = None  # the node left between the listing and the question
      if reply is not None:
        found["nodes"][node] = {
          k: v for k, v in json.loads(reply.data).items() if k != "ok"
        }
    for entry in runtime.directory.entries():
      if entry.kind not in ("runtime", NODE_KIND):
        found["components"].append({"kind": entry.kind, "name": entry.name})
    return found

  async def stop_watching() -> None:
    """Close the report connection while its server is still there."""
    for opened in watching.values():
      await opened.close()
    watching.clear()

  if not dev:
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
          await until(lambda: _count(report(d), "alpha", 1)),
          None,
        )
        beta = await long_running(d, "dev", "--name", "beta")
        check(
          "a second node joins the same deployment",
          await until(lambda: _count(report(d), "beta", 1)),
          None,
        )

        async def both_listed() -> bool:
          body = await cli_report(d)
          probes = [c for c in body["components"] if c["name"] == "probe"]
          return sorted(body["nodes"]) == ["alpha", "beta"] and len(probes) == 2

        check(
          "ps lists both nodes and their components",
          await until(both_listed),
          await cli_report(d),
        )

        code, out = await cli(d, "dev", "--name", "alpha")
        check(
          "a node name can only run once",
          code == 1 and "already running" in out,
          (code, out),
        )
        code, out = await cli(d, "dev", "scale", "app", "2")
        check(
          "scale without --node is ambiguous with two nodes",
          code == 1 and "Several nodes" in out,
          (code, out),
        )
        code, out = await cli(d, "dev", "scale", "app", "2", "--node", "alpha")
        check("scale --node targets one node", code == 0, (code, out))
        body = await report(d)
        sizes = {n: len(v["processes"]) for n, v in body["nodes"].items()}
        check("only that node changed", sizes == {"alpha": 2, "beta": 1}, sizes)
        before = {c["pid"] for c in body["nodes"]["beta"]["processes"]}
        code, out = await cli(d, "dev", "roll", "app", "--node", "beta")
        after = {c["pid"] for c in (await report(d))["nodes"]["beta"]["processes"]}
        check(
          "roll replaces every process of that node",
          code == 0 and not (before & after) and len(after) == 1,
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
        await stop_watching()
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

  if dev:
    with tempfile.TemporaryDirectory() as raw:
      d = Path(raw)
      port = free_port()
      project(d, port)
      up = await long_running(d, "dev")
      try:
        check(
          "micro dev runs the server and the processes together",
          await until(lambda: _count(report(d), None, 1), 30)
          and await reachable("127.0.0.1", port),
        )
        await stop_watching()
        code = await ctrl_c(up)
        check(
          "Ctrl-C stops the processes, then the server it started",
          code == 0 and not await reachable("127.0.0.1", port),
          code,
        )
      finally:
        if up.returncode is None:
          os.killpg(up.pid, signal.SIGKILL)


async def _count(
  body: Awaitable[dict[str, Any]], node: str | None, expected: int
) -> bool:
  nodes = (await body)["nodes"]
  if node is None:
    return any(len(v["processes"]) == expected for v in nodes.values())
  return node in nodes and len(nodes[node]["processes"]) == expected


async def _micro_process(directory: Path, *args: str) -> tuple[int, str]:
  """`micro ...` as its own process, for what depends on the real environment."""
  proc = await asyncio.create_subprocess_exec(
    sys.executable,
    "-m",
    "micro",
    *args,
    cwd=directory,
    env=os.environ | {"PATH": os.environ["PATH"]},
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.STDOUT,
  )
  out, _ = await asyncio.wait_for(proc.communicate(), 60)
  return proc.returncode or 0, out.decode()


async def _micro(directory: Path, *args: str, merge: bool = True) -> tuple[int, str]:
  """`micro ...` run in this process (the scenario is forked, so its directory and
  environment are its own): a process per command is most of what these tests cost."""
  import contextlib
  import io

  from micro import cli as micro_cli

  def run() -> tuple[int, str]:
    out = io.StringIO()
    err = out if merge else io.StringIO()
    code: Any = 0
    before = os.getcwd()
    os.chdir(directory)
    try:
      with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
          code = micro_cli.main(list(args))
        except SystemExit as stop:
          code = stop.code or 0
    finally:
      os.chdir(before)
    return int(code), out.getvalue()

  return await asyncio.to_thread(run)


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


async def _pkg_phase(phase: str) -> None:
  """One part of the package tests, on an upstream repository of its own (so the
  parts can run side by side)."""
  from micro.scaffold import Project, _sources, packages
  from micro.scaffold import _git as scaffold_git

  saved = os.environ.get("MICRO_PACKAGES_URL")
  with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    repo = _upstream(root)
    os.environ["MICRO_PACKAGES_URL"] = repo.as_uri()
    first = _git(repo, "rev-parse", "HEAD")
    try:
      if phase == "cli":
        await _pkg_cli(root, repo, first)
      elif phase == "merging":
        await _pkg_merging(root, repo, first, Project, packages)
      elif phase == "refs":
        await _pkg_refs_and_sources(root, repo, first, Project, packages, _sources)
      else:
        await _pkg_environment(root, scaffold_git)
    finally:
      if saved is None:
        os.environ.pop("MICRO_PACKAGES_URL", None)
      else:
        os.environ["MICRO_PACKAGES_URL"] = saved


async def pkg_cli_scenarios() -> None:
  print("pkg: the command line")
  await _pkg_phase("cli")


async def pkg_merging_scenarios() -> None:
  print("pkg: merging upgrades")
  await _pkg_phase("merging")


async def pkg_refs_scenarios() -> None:
  print("pkg: refs and sources")
  await _pkg_phase("refs")


async def pkg_environment_scenarios() -> None:
  print("pkg: the environment")
  await _pkg_phase("environment")


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
  code, out = await _micro(d, "pkg", "add", "builtin/chat")
  check(
    "pkg add copies a package",
    code == 0 and (d / "services/chat/__init__.py").is_file(),
    out,
  )
  code, out = await _micro(d, "pkg", "add", "builtin/ticker")
  code, out = await _micro(d, "pkg", "add", "builtin/tpl", "tickets")
  text = (d / "services/tickets/__init__.py").read_text() if code == 0 else ""
  check("a template is filled in with its name", 'name = "tickets"' in text, out + text)
  code, out = await _micro(d, "pkg", "add", "builtin/tpl")
  code, out = await _micro(d, "pkg", "add", "builtin/nope")
  code, out = await _micro(d, "pkg", "add", "builtin/chat")
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
  code, out = await _micro(d, "services", "list")
  code, out = await _micro(d, "pkg", "forget", "tickets")
  code, out = await _micro(d, "pkg", "status", "tickets")


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
  _release_two(repo)
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
  packages.Lock.load(project).entries["demo"]
  after = {c.file: c.kind for c in packages.status(project)[0].changes}
  (folder / "clash.py").write_text("a = 1\nb = 77\nc = 3\nd = 4\n")  # you resolve it
  (folder / "gone.py").write_text(
    "a = 1\nb = 2\nc = 3\nd = 40\n"
  )  # and bring gone back
  after = {c.file: c.kind for c in packages.status(project)[0].changes}
  packages.diff(project, "demo")

  # --theirs and --mine, from a fresh copy.
  _git(repo, "rev-parse", "HEAD")
  project, folder = fresh("theirs")
  packages.upgrade(project, ref="main", settle="theirs")
  check(
    "--theirs takes upstream's file for every conflict and brings a deleted file back",
    (folder / "both.py").read_text() == "a = 1\nb = 2\nc = 3\nd = 40\n"
    and (folder / "clash.py").read_text() == "a = 1\nb = 22\nc = 3\nd = 4\n"
    and (folder / "gone.py").exists(),
  )
  packages.Lock.load(project).entries["demo"]
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
  code, out = await _micro(d, "pkg", "add", "billing")
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
  code, out = await _micro(d, "pkg", "source", "remove", "nope")
  # Refs: a tag pins, a branch follows.
  code, out = await _micro(d, "pkg", "add", "builtin/ticker", "--ref", "v1")
  lock = (d / "micro.lock").read_text()
  check("--ref pins a tag and records it", code == 0 and 'ref = "v1"' in lock, out)
  code, out = await _micro(d, "pkg", "add", "builtin/hello", "hello2", "--ref", "nope")
  code, out = await _micro(d, "pkg", "upgrade", "--ref", "main")


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
    code, out = await _micro_process(d2, "init")
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
  async def echo(ctx: Context, request: Say) -> str:
    return request.text

  @service.handle(SECRET)
  async def secret(ctx: Context, request: Say) -> str:
    return "the secret"

  @service.handle(OTHER)
  async def other(ctx: Context, request: Say) -> str:
    return "unreachable"

  DROPS = RequestSchema[Say, str](id="mw.drops", input=Say, output=str)
  LOOKS = RequestSchema[Say, str](id="mw.looks", input=Say, output=str)

  @service.handle(DROPS)
  async def drops(ctx: Context, request: Say) -> str:
    from micro.result import Err

    Err(ValueError("a failure nobody looked at"))
    return "fine"

  @service.handle(LOOKS)
  async def looks(ctx: Context, request: Say) -> str:
    from micro.result import Err

    return Err(ValueError("looked at")).unwrap_or("fine")

  @service.listen(HAPPENED)
  async def happened(ctx: Context, event: Say) -> None:
    trace.append(f"event:{event.text}")
    if event.text == "flaky" and flaky["left"]:
      flaky["left"] -= 1
      raise RuntimeError("try again")

  @service.work(QUEUE)
  async def job(ctx: Context, item: Say) -> None:
    trace.append(f"job:{item.text}")

  async with Stack(App()) as s:
    await s.runtime.add(service)
    client = service.client
    check(
      "input and output rewritten", await client.request(ECHO, Say(text="hi")) == "HI!"
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
    try:
      await client.request(DROPS, Say(text="x"))
      dropped = ""
    except RemoteError as error:
      dropped = f"{error.code} {error.message}"
    check(
      "a handler that drops an error result fails, naming it and where it was made",
      "handler_failed" in dropped
      and "never looked at" in dropped
      and "a failure nobody looked at" in dropped
      and "drops" in dropped,
      dropped,
    )
    trace.clear()
    await client.emit(HAPPENED, Say(text="skip"))
    await client.emit(HAPPENED, Say(text="ok"))
    await s.fake.until(lambda: "event:ok" in trace, 8)
    await asyncio.sleep(0.3)
    check("end() on an event skips its handler", "event:skip" not in trace, trace)
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

  consumer_module._FETCH_WAIT = 0.2  # pyright: ignore[reportPrivateUsage]
  from micro.discord.interactions import PatternRoute
  from micro.discord.interactions._pattern import literal_head

  check("literal head of a regex", literal_head(r"ticket\.(?P<a>\w+)") == "ticket.")
  check("quantified literal is not part of the head", literal_head(r"abc?d") == "ab")
  check("no head for a leading class", literal_head(r"\d+x") == "")
  check("template prefix", PatternRoute.template("a.{b}:{c}").prefix == "a.")

  service = Service("panel")
  components = Components(service)

  def says(text: str) -> Callable[[Context, Interaction], Awaitable[None]]:
    async def handler(ctx: Context, interaction: Interaction) -> None:
      await interaction.respond(f"{text} {dict(interaction.route)}")

    return handler

  components.match("ticket.{action}:{id:\\d+}")(says("template"))
  components.match(re.compile(r"report\.(?P<kind>spam|abuse)"))(says("regex"))
  components.match(SignedRoute())(says("custom"))
  components.match(CustomId("legacy"))(says("legacy"))

  async with Stack(App()) as s:
    await s.runtime.add(service)
    await s.fake.until(
      lambda: any(
        e.name == service.name for e in s.runtime.directory.entries("service")
      ),
      8,
    )
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
    Embed,
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
    Button(
      "Go",
      custom_id="a",
      style=ButtonStyle.PRIMARY,
      emoji=Emoji.parse("🙂"),
      disabled=True,
      id=1,
    ),
  )
  for st in (ButtonStyle.SECONDARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER):
    case(f"button {st.name.lower()}", Button("x", custom_id="a", style=st))
  case(
    "button custom emoji",
    Button("x", custom_id="a", emoji=Emoji.parse("<a:wave:1234567890>")),
  )
  case("button link", Button("Docs", url="https://example.com/x", emoji=Emoji("📖")))
  case("button premium", Button(sku_id=123456789012345678))
  case(
    "action row of buttons",
    ActionRow(*[Button(str(i), custom_id=f"b{i}") for i in range(5)], id=2),
  )
  opts = [
    SelectOption("A", "a", "first", True, Emoji.parse("🅰")),
    SelectOption("b"),
    SelectOption("C", "c", emoji=Emoji.parse("<:c:123456789>")),
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
          ChannelType.GUILD_TEXT,
          ChannelType.GUILD_VOICE,
          ChannelType.GUILD_CATEGORY,
          ChannelType.GUILD_ANNOUNCEMENT,
          ChannelType.PUBLIC_THREAD,
          ChannelType.GUILD_FORUM,
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
      TextDisplay("a"),
      TextDisplay("b"),
      TextDisplay("c"),
      accessory=Thumbnail("https://e.com/i.png", "alt", True),
    ),
  )
  case(
    "section + button",
    Section(TextDisplay("click"), accessory=Button("Go", custom_id="x")),
  )
  case(
    "media gallery",
    MediaGallery(
      MediaItem("https://e.com/a.png"), MediaItem("attachment://b.png", "desc", True)
    ),
  )
  case("file", File("attachment://report.pdf", spoiler=True))
  case("separator", [Separator(), Separator(divider=False, spacing="large")])
  case(
    "container",
    Container(
      TextDisplay("hello"),
      Separator(),
      Section(TextDisplay("s"), accessory=Thumbnail("https://e.com/i.png")),
      MediaGallery(MediaItem("https://e.com/a.png")),
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
        style=TextInputStyle.PARAGRAPH,
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
    Label(
      "Pick", StringSelect("p", [SelectOption("x"), SelectOption("y")], required=True)
    ),
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
    Label("Chan", ChannelSelect("c", channel_types=[ChannelType.GUILD_TEXT])),
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
      RadioGroup(
        "rg",
        [GroupOption("A", "a", "d", True), GroupOption("b"), GroupOption("c")],
        required=True,
      ),
    ),
    modal=True,
  )
  case(
    "modal checkbox group",
    Label(
      "Many",
      CheckboxGroup("cg", [GroupOption("a"), GroupOption("B", "b")], 0, 2, False),
    ),
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
      Label("Opts", CheckboxGroup("c", [GroupOption("a"), GroupOption("b")])),
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
  for extra in ({"content": "hi"}, {"embeds": [Embed("t")]}):
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
  from dataclasses import dataclass as _dataclass

  @_dataclass(frozen=True, slots=True)
  class Danger(Button):
    """A subclass: it has everything its parent has, with no table to add it to."""

  long = Danger("x" * 81, custom_id="a")
  try:
    long.to_dict()
    refused_long = False
  except ValueError:
    refused_long = True
  check(
    "a subclass of a component inherits its limits, max and counts (class fields)",
    Danger.code == Button.code == 2
    and Danger.max == Button.max == 80
    and Danger.limits is Button.limits
    and long.count == 81
    and long.remaining == -1
    and refused_long
    and ActionRow(Danger("ok", custom_id="b")).count == 1,
  )

  class Wide(Embed):
    pass

  check(
    "and so does a subclass of Embed",
    Wide.limits is Embed.limits and Wide.footer_limit == Embed.footer_limit == 2048,
  )
  from micro.discord.interactions import Interaction

  def interaction_of(data: dict[str, Any], kind: int = 5) -> Interaction:
    payload = {
      "id": "1",
      "token": "t",
      "application_id": "1",
      "guild_id": "7",
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
    submitted.submitted.inputs
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
    submitted.submitted.inputs,
  )
  check(
    "fields keeps to text inputs and radios, as strings",
    submitted.submitted.fields
    == {"name": "Ada", "radio": "b", "radio_none": "", "legacy": "old"},
    submitted.submitted.fields,
  )
  check(
    "what a handler receives is bound to its context, so its actions work",
    submitted.user.context is submitted.context
    and all(u.context is submitted.context for u in submitted.submitted.users("who"))
    and all(
      r.guild_id == "7" and r.context is submitted.context
      for r in submitted.submitted.roles("role")
    ),
  )
  check(
    "selected entities resolve to typed objects",
    [u.username for u in submitted.submitted.users("who")] == ["ann", "bob"]
    and [m.nick for m in submitted.submitted.members("who")] == ["A"]
    and [r.name for r in submitted.submitted.roles("role")] == ["mods"]
    and [c.name for c in submitted.submitted.channels("chan")] == ["general"]
    and [(a.filename, a.size) for a in submitted.submitted.attachments("files")]
    == [("a.png", 5), ("b.txt", 7)]
    and submitted.submitted.choices("color") == ["red", "blue"],
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
    "a mentionable select gives users and roles from interaction directly",
    [u.username for u in menu.submitted.users()] == ["ann"]
    and [r.name for r in menu.submitted.roles()] == ["mods"],
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
    User.model_validate(user).accent_colour == 123
    and type(full).__name__ == "UserResponse"
    and partial_refused,
  )
  try:
    ui.validate(Button("x", custom_id="a" * 101))
    caught = False
  except ValueError as error:
    caught = "100" in str(error)
  check("validate() reports Discord's own limits", caught)


async def api_scenarios() -> None:
  print("api: every operation as a method, checked on the wire")
  import inspect
  from datetime import UTC, datetime
  from email import message_from_bytes
  from email.policy import default as email_policy

  import httpx2
  from pydantic import ValidationError

  from micro.discord import http_service, ui

  # A 502/503/504 is retried after a backoff (1 s, 2 s, 4 s, ...); a test of the
  # retrying needs the retries, not the seconds.
  http_service.default_backoff = lambda attempt: 0.01 * attempt

  # Structure: every operation is a method whose parameters match its request model.
  from micro.discord._api import _body_fields  # pyright: ignore[reportPrivateUsage]
  from micro.discord.api import DiscordAPI, Upload
  from micro.discord.http_operations import HTTP_OPERATIONS
  from micro.discord.http_service import DiscordAPIError, NotFound
  from micro.result import Err

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
      if n not in ("self", "body", "content", "message")
      and p.kind is p.POSITIONAL_OR_KEYWORD
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
    if "body" in request and {"embeds", "components"} <= wanted:
      # A message operation takes a Draft for everything a Draft carries.
      wanted -= {"content", "embeds", "components", "allowed_mentions", "tts", "flags"}
      wanted -= {"message_reference", "attachments"}
      if "message" not in params:
        gaps.append(f"{op.id}: no message=")
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
        sent = (
          await api.create_message(
            5,
            ui.Draft(
              "@everyone hello",
              embeds=[
                ui.Embed(
                  "T",
                  "D",
                  timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                  footer=ui.EmbedFooter("f", "https://e.com/i.png"),
                )
              ],
              components=[
                ui.Button("Go", custom_id="go"),
                ui.StringSelect("s", [ui.SelectOption("a"), ui.SelectOption("b")]),
              ],
            ),
          )
        ).unwrap()
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
        (
          await api.create_message(
            5,
            ui.Draft(
              components=[ui.Container(ui.TextDisplay("hi"), accent_colour=0xFF0000)]
            ),
          )
        ).unwrap()
        body = json_of(seen[-1])
        (
          await api.create_message(
            5,
            ui.Draft(
              "with files",
              embeds=[ui.Embed("T")],
              files=[
                Upload("cat.png", b"\x89PNG-data", "image/png"),
                Upload("notes.txt", b"plain"),
              ],
            ),
            reason="because",
          )
        ).unwrap()
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

        (await api.update_message(5, 9, "edited")).unwrap()
        call = seen[-1]
        (await api.delete_message(5, 9, reason="spam & ünïcode")).unwrap()
        call = seen[-1]
        answers["GET /channels/5/messages"] = (200, [message])
        (await api.list_messages(5, limit=3, before=7)).unwrap()
        await api.bulk_set_application_commands(
          100, [{"name": "ping", "description": "p", "type": 1}]
        )
        body = json_of(seen[-1])
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
        answers["PUT /guilds/7/bans/8"] = (
          403,
          {"code": 50013, "message": "Missing Permissions"},
        )
        banned = await api.ban_user_from_guild(
          7, 8, delete_message_seconds=60, reason="r"
        )
        caught = banned.error if isinstance(banned, Err) else None
        check(
          "a Discord error comes back as an Err holding the DiscordAPIError, with the status and body",
          caught is not None
          and caught.status == 403
          and isinstance(caught.body, dict)
          and caught.body["code"] == 50013,
          caught,
        )
        # Refs: an object by id, with its ids bound.
        from datetime import UTC
        from datetime import datetime as when

        (
          await api.channel(5).send(ui.Draft("via ref", embeds=[ui.Embed("E")]))
        ).unwrap()
        (await api.message(5, 9).reply("yo")).unwrap()
        check(
          "message.reply sets message_reference to the message",
          json_of(seen[-1])["message_reference"]["message_id"] == "9"
          and seen[-1]["path"] == "/channels/5/messages",
          json_of(seen[-1]),
        )
        await api.message(5, 9).react("👍")
        await api.message(5, 9).react(ui.Emoji("wave", 123456))
        await api.member(7, 8).kick(reason="rule 1")
        await api.member(7, 8).add_role(20)
        until = when(2030, 1, 2, 3, 4, 5, tzinfo=UTC)
        await api.member(7, 8).timeout(until, reason="cool off")
        await api.member(7, 8).timeout(None)
        answers.pop("PUT /guilds/7/bans/8", None)  # it answered 403 for the error check
        await api.guild(7).ban(8, delete_message_seconds=60, reason="r")
        answers["POST /users/@me/channels"] = (
          200,
          {"id": "55", "type": 1, "recipients": []},
        )
        (await api.user(8).send("hello there")).unwrap()
        opened, sent_dm = seen[-2], seen[-1]
        check(
          "user.send opens the DM, then sends to it",
          opened["path"] == "/users/@me/channels"
          and json_of(opened) == {"recipient_id": "8"}
          and sent_dm["path"] == "/channels/55/messages",
          (opened["path"], sent_dm["path"]),
        )
        (await api.webhook_token(3, "tok").execute("hook", wait=True)).unwrap()
        await api.channel(5).edit(topic=None, name="renamed")

        # Interaction shortcuts reach the same methods.
        payload = {
          "id": "1", "token": "tk", "application_id": "100", "type": 2, "guild_id": "7",
          "channel_id": "5", "data": {"name": "x"}, "member": {"user": {"id": "8", "username": "u"}, "roles": []},
          "message": {"id": "9", "channel_id": "5"},
        }  # fmt: skip
        from micro.discord.interactions import Interaction

        interaction = Interaction(payload, DiscordHTTPClient(runtime))
        (await interaction.channel_ref.send("from interaction")).unwrap()
        await interaction.member_ref.add_role(30)
        await interaction.message_ref.pin()
        await interaction.guild_ref.unban(8)

        before = len(seen)
        try:
          await api.create_message(5, enforce_nonce="maybe")  # type: ignore[arg-type]
          refused = False
        except ValidationError:
          refused = True

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
        # Interaction responses carry files too.
        from micro.discord.interactions import Interaction

        def multipart(call: dict[str, Any]) -> tuple[Any, dict[Any, Any]]:
          envelope = message_from_bytes(
            b"Content-Type: "
            + call["headers"]["content-type"].encode()
            + b"\r\n\r\n"
            + call["body"],
            policy=email_policy,
          )
          found = {
            part.get_param("name", header="content-disposition"): part
            for part in envelope.iter_parts()
          }
          return json.loads(found["payload_json"].get_content()), found

        def make_interaction(**more: Any) -> Any:
          return Interaction(
            {"id": "77", "token": "tok", "application_id": "100", "type": 2,
             "data": {"name": "x"}, "user": {"id": "1"}, **more},
            api.http,
          )  # fmt: skip

        picture = Upload("cat.png", b"\x89PNG", "image/png")
        interaction = make_interaction()
        await interaction.respond(Draft("look", files=[picture], ephemeral=True))
        payload, found = multipart(seen[-1])
        check(
          "respond(files=...) uploads with the first response",
          seen[-1]["path"] == "/interactions/77/tok/callback"
          and payload["type"] == 4
          and payload["data"]["content"] == "look"
          and payload["data"]["flags"] & ui.EPHEMERAL
          and found["files[0]"].get_filename() == "cat.png"
          and found["files[0]"].get_payload(decode=True) == b"\x89PNG",
          (seen[-1]["path"], payload),
        )
        answers["POST /webhooks/100/tok"] = (200, message)
        await interaction.respond(Draft("more", files=[picture]))
        payload, found = multipart(seen[-1])
        check(
          "a follow-up carries files",
          seen[-1]["path"] == "/webhooks/100/tok"
          and payload["content"] == "more"
          and "files[0]" in found,
          (seen[-1]["path"], payload),
        )
        answers["PATCH /webhooks/100/tok/messages/@original"] = (200, message)
        interaction = make_interaction()
        await interaction.defer(thinking=True, ephemeral=True)
        await interaction.respond(
          Draft(components=[ui.Container(ui.TextDisplay("done"))], ephemeral=True)
        )
        body = json_of(seen[-1])
        check(
          "answering after thinking keeps the components-v2 flag and drops the rest",
          seen[-1]["method"] == "PATCH" and body.get("flags") == ui.IS_COMPONENTS_V2,
          body,
        )
        interaction = make_interaction()
        await interaction.defer(thinking=True)
        await interaction.respond("plain")
        chart = Upload("chart.png", b"png", description="Sales by week")
        interaction = make_interaction()
        await interaction.respond(
          Draft(
            components=[
              ui.Container(
                ui.Section(ui.TextDisplay("Sales"), accessory=ui.Thumbnail(chart)),
                ui.MediaGallery(
                  ui.MediaItem(chart), ui.MediaItem(Upload("b.png", b"b", spoiler=True))
                ),
                ui.File(Upload.text("log.txt", "all good")),
              )
            ]
          )
        )
        payload, found = multipart(seen[-1])
        inner = payload["data"]["components"][0]["components"]
        check(
          "an Upload shown by a component is attached by itself, once",
          sorted(k for k in found if k != "payload_json")
          == ["files[0]", "files[1]", "files[2]"]
          and found["files[0]"].get_filename() == "chart.png"
          and inner[0]["accessory"]["media"]["url"] == "attachment://chart.png"
          and inner[1]["items"][0]["media"]["url"] == "attachment://chart.png"
          and inner[2]["file"]["url"] == "attachment://log.txt"
          and found["files[2]"].get_payload(decode=True) == b"all good",
          (list(found), inner),
        )
        interaction = make_interaction()
        await interaction.respond(Draft(embeds=[ui.Embed("T", image=chart)]))
        payload, found = multipart(seen[-1])
        try:
          ui.uploads_in(files=[Upload("a.txt", b"1"), Upload("a.txt", b"2")])
        except ValueError:
          pass
        await interaction.edit_response(
          Draft("v2", files=[Upload("new.txt", b"n")], keep=["555"])
        )
        payload, found = multipart(seen[-1])
        check(
          "an edit says which existing files stay, and adds the new ones",
          payload["attachments"] == [{"id": "555"}, {"id": "0", "filename": "new.txt"}]
          and "files[0]" in found,
          payload,
        )
        (
          await api.create_message(
            5, ui.Draft(components=[ui.MediaGallery(ui.MediaItem(chart))])
          )
        ).unwrap()
        payload, found = multipart(seen[-1])

        interaction = make_interaction()
        await interaction.respond(
          ui.Draft(
            "from a draft",
            embeds=[ui.Embed("T", image=chart)],
            ephemeral=True,
          )
        )
        payload, found = multipart(seen[-1])
        check(
          "interaction.respond(Draft) sends the draft, its uploads included",
          payload["data"]["content"] == "from a draft"
          and payload["data"]["flags"] & ui.EPHEMERAL
          and "files[0]" in found,
          payload,
        )
        await api.create_message(5, ui.Draft("api draft", embeds=[ui.Embed("E")]))
        await api.create_message(
          5, ui.Draft(components=[ui.MediaGallery(ui.MediaItem(chart))])
        )
        payload, found = multipart(seen[-1])
        (await api.channel(5).send(ui.Draft("via ref", reply_to=9))).unwrap()
        interaction = make_interaction()
        await interaction.defer(thinking=True)
        await interaction.respond(ui.Draft("done"))
        await interaction.edit_response(ui.Draft(embeds=()))
        check(
          "editing with a Draft clears what is empty and keeps what is None",
          json_of(seen[-1])["embeds"] == [] and "content" not in json_of(seen[-1]),
          json_of(seen[-1]),
        )

        # A gateway error is retried only where sending twice cannot act twice.
        answers["GET /guilds/777"] = (504, {"message": "upstream"})
        before = len(seen)
        late_gateway = await api.guild(777).get()
        gave_up = isinstance(late_gateway, Err) and late_gateway.error.status == 504
        check(
          "a 504 on a GET is retried (it is idempotent)",
          gave_up and len(seen) - before == 4,
          len(seen) - before,
        )
        answers["POST /channels/777/messages"] = (504, {"message": "upstream"})
        before = len(seen)
        refused = await api.create_message(777, "once")
        gave_up = isinstance(refused, Err) and refused.error.status == 504
        check(
          "a 504 on a POST is not: it may have been carried out",
          gave_up and len(seen) - before == 1,
          len(seen) - before,
        )
        check(
          "Discord's refusal comes back as an Err; unwrap() raises the same error",
          isinstance(refused, Err)
          and isinstance(refused.error, DiscordAPIError)
          and refused.ok() is None
          and refused.unwrap_or("fallback") == "fallback",
        )
        try:
          refused.unwrap()
        except DiscordAPIError:
          pass  # pyright: ignore[reportAttributeAccessIssue]
        answers["GET /channels/5/messages/404"] = (
          404,
          {"code": 10008, "message": "Unknown Message"},
        )
        match await api.get_message(5, 404):
          case Err(NotFound()):
            pass
          case _:
            pass
        (await api.get_message(5, 404)).ignore(NotFound)
        answers["GET /channels/5/messages/9"] = (200, message)
        found = await api.get_message(5, 9)

        from micro.discord.interactions._context import REPLY_KEY

        inline: list[Any] = []

        async def on_inline(msg: Any) -> None:
          inline.append(json.loads(msg.data))

        held = await runtime.nats.subscribe("test.inline", cb=on_inline)
        interaction = make_interaction(**{REPLY_KEY: "test.inline"})
        await interaction.respond(Draft("over http", files=[picture], ephemeral=True))
        await runtime.nats.flush()
        payload, found = multipart(seen[-1])
        check(
          "an interaction received over HTTP acknowledges inline, then sends the files",
          inline == [{"type": 5, "data": {"flags": ui.EPHEMERAL}}]
          and seen[-1]["method"] == "PATCH"
          and payload["content"] == "over http"
          and "flags" not in payload
          and "files[0]" in found
          and interaction.state.name == "MESSAGE",
          (inline, payload, interaction.state),
        )
        await held.unsubscribe()

        # A burst on one route waits for Discord's first answer instead of all going
        # at once (and all but a few coming back as 429s).
        from micro.discord.http_service import DiscordHTTPResponse, RateLimits

        limits = RateLimits()
        out = 0
        peak = 0
        sent_at_once: list[int] = []

        async def one(index: int) -> None:
          nonlocal out, peak
          await limits.acquire("r:1")
          out += 1
          peak = max(peak, out)
          sent_at_once.append(out)
          await asyncio.sleep(0.01)
          out -= 1
          left = max(4 - index, 0)
          await limits.observe(
            "r:1",
            DiscordHTTPResponse(
              status=200,
              headers=(
                ("x-ratelimit-limit", "5"),
                ("x-ratelimit-remaining", str(left)),
                ("x-ratelimit-reset-after", "0.2"),
                ("x-ratelimit-bucket", "b"),
              ),
              body=b"",
            ),
          )

        started = time.monotonic()
        await asyncio.gather(*(one(i) for i in range(8)))
        took = time.monotonic() - started
        check(
          "a burst sends one request, learns the limit, then stays within it",
          sent_at_once[0] == 1 and peak <= 4 and took >= 0.2,
          (sent_at_once, peak, round(took, 2)),
        )
        quiet = RateLimits()

        async def unlimited() -> None:
          await quiet.acquire("q")
          await asyncio.sleep(0.01)
          await quiet.observe(
            "q", DiscordHTTPResponse(status=204, headers=(), body=b"")
          )

        await unlimited()
        started = time.monotonic()
        await asyncio.gather(*(unlimited() for _ in range(20)))
        stuck = RateLimits()
        await stuck.acquire("s")
        await stuck.abandon("s")
        await asyncio.wait_for(stuck.acquire("s"), 1)
        check("a request that got no answer does not block the next one", True)

        before = len(seen)
        try:
          await api.channel(5).get()
          refused = False
        except Exception as error:
          refused = "off limits" in str(error)
        undo()
        undo_refuse()
        unhook()
        len(late)
        await api.channel(5).get()
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
  async def on_remind(ctx: Context, note: Note) -> None:
    arrivals.append(("event", note.text, time.monotonic() - started))

  @service.work(CHORE)
  async def on_chore(ctx: Context, note: Note) -> None:
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

    ticks = {"first": 0, "second": 0}

    def replica(name: str) -> Service:
      each = Service("every-demo")

      @each.every(0.05)
      async def tick(ctx: Context) -> None:
        ticks[name] += 1

      tick.__qualname__ = "tick"  # the same task on every replica
      return each

    steps: list[str] = []
    lifecycle = Service("lifecycle-demo")

    @lifecycle.startup
    async def opened(ctx: Context) -> None:
      steps.append("startup")

    @lifecycle.shutdown
    async def closed(ctx: Context) -> None:
      steps.append("shutdown")

    await runtime.add(lifecycle)
    started_first = list(steps)
    await lifecycle.drain()
    await lifecycle.close()
    check(
      "startup runs when the service starts and shutdown when it closes, no subclass needed",
      started_first == ["startup"] and steps == ["startup", "shutdown"],
      (started_first, steps),
    )

    first, second = replica("first"), replica("second")
    await runtime.add(first)
    await eventually(lambda: asyncio.sleep(0, ticks["first"]), lambda n: n >= 2)
    await runtime.add(second)
    await asyncio.sleep(0.4)
    waiting = ticks["second"] == 0
    await first.drain()
    await first.close()
    took_over = await eventually(
      lambda: asyncio.sleep(0, ticks["second"]), lambda n: n >= 2
    )
    check(
      "every runs on one replica at a time, and another takes over when it goes away",
      waiting and took_over is not None and took_over >= 2,
      ticks,
    )

    now = time.monotonic() - started
    await timers.event("t.event", REMIND, Note(text="soon"), after=0.4)
    await timers.job("t.job", CHORE, Note(text="chore"), after=0.5)
    check(
      "an event timer fires at its time",
      await waited("event", "soon", 6) and 0.3 <= got("event", "soon")[0] - now <= 3.0,
      got("event", "soon"),
    )
    check("a job timer reaches a worker", await waited("job", "chore", 6), arrivals)

    await timers.event("t.replace", REMIND, Note(text="first"), after=0.3)
    await timers.event("t.replace", REMIND, Note(text="second"), after=0.8)
    await waited("event", "second", 6)  # the first would be due well before this
    check(
      "scheduling a key again replaces it: only the new one fires",
      got("event", "first") == [] and len(got("event", "second")) == 1,
      arrivals,
    )

    await timers.event("t.cancel", REMIND, Note(text="never"), after=0.4)
    await timers.event("t.canary", REMIND, Note(text="canary"), after=0.9)
    check("cancel removes a timer", await timers.cancel("t.cancel") is True)
    await waited("event", "canary", 6)  # it comes due after the cancelled one would

    await timers.event(
      "t.past", REMIND, Note(text="late"), at=when.now(UTC) - timedelta(minutes=5)
    )

    # No scheduler running: timers wait, then are delivered when one starts.
    await scheduler.close()
    await timers.event("t.catchup", REMIND, Note(text="caught"), after=0.3)
    await asyncio.sleep(1.0)
    check(
      "with no scheduler, a due timer waits", got("event", "caught") == [], arrivals
    )
    await timers.pending("t.")
    replacement = Scheduler("scheduler")
    await runtime.add(replacement)
    check(
      "a new scheduler delivers what came due meanwhile",
      await waited("event", "caught", 6),
      arrivals,
    )

    # Two schedulers share the work: every timer is delivered exactly once.
    second = Scheduler("scheduler")
    await runtime.add(second)
    for n in range(8):
      await timers.event(f"t.many.{n}", REMIND, Note(text=f"m{n}"), after=0.3)
    for n in range(8):
      await waited("event", f"m{n}", 6)
    await asyncio.sleep(0.6)  # a duplicate would arrive about now
    counts = [len(got("event", f"m{n}")) for n in range(8)]
    check("two schedulers deliver each timer exactly once", counts == [1] * 8, counts)

    # Listing and lookup.
    soon = when.now(UTC) + timedelta(hours=1)
    later = when.now(UTC) + timedelta(hours=2)
    await timers.job("list.b", CHORE, Note(text="b"), at=later)
    await timers.event("list.a", REMIND, Note(text="a"), at=soon)
    await timers.pending("list.")
    await timers.get("list.b")
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

    await ask(engine, 'mutation { addGuild(id: "1", name: "Home") { id name prefix } }')
    dup = await ask(engine, 'mutation { addGuild(id: "1", name: "Again") { id } }')
    check(
      "inserting an existing key is a CONFLICT error",
      dup["data"] is None and dup["errors"][0]["extensions"]["code"] == "CONFLICT",
      dup,
    )
    await ask(
      engine,
      'mutation { addCommand(guildId: "1", name: "hello", body: "hi") { uses tags enabled } }',
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

    await ask(engine, 'mutation { bump(guildId: "1", name: "hello") { uses } }')
    again = await ask(engine, 'mutation { bump(guildId: "1", name: "hello") { uses } }')
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
    await ask(
      engine, 'mutation { editBody(guildId: "1", name: "hello") { body uses } }'
    )
    cleared = await ask(
      engine, 'mutation { editBody(guildId: "1", name: "hello", body: null) { body } }'
    )
    check(
      "an explicit null clears a field",
      cleared["data"]["editBody"]["body"] is None,
      cleared,
    )
    await ask(
      engine, 'mutation { editBody(guildId: "1", name: "nope", body: "x") { body } }'
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
    await ask(engine, '{ guild(id: "1") { commands { name } } }')

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
    await ask(engine, '{ allCommands(first: 5000, offset: 0) { name } }')

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
    await ask(engine, '{ note(id: "1") { text pinned } }')
    await engine.apply_modules(
      [GraphModule(id="cmds", schema=commands), GraphModule(id="notes", schema=v3)]
    )
    await engine.apply_modules(
      [GraphModule(id="cmds", schema=commands), GraphModule(id="notes", schema=v2)]
    )
    await ask(engine, '{ note(id: "1") { text } }')
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
      await client.execute(
        'query($n: ID!) { tag(name: $n) { uses } }', variables={"n": "py"}
      )


SCENARIOS: dict[str, Callable[[], Awaitable[None]]] = {
  "basics": basics,
  "sync": sync_scenarios,
  "runtime-commands": runtime_command_scenarios,
  "idle": idle_scenarios,
  "config": config_scenarios,
  "gateway-config": gateway_config_scenarios,
  "handover": handover_scenarios,
  "docs": docs_scenarios,
  "ui-limits": ui_limits_scenarios,
  "logging": logging_scenarios,
  "errors": error_hook_scenarios,
  "helpers": helper_scenarios,
  "state": state_scenarios,
  "endpoint": endpoint_scenarios,
  "custom": custom_package_scenarios,
  "cli": cli_scenarios,
  "cli-dev": cli_dev_scenarios,
  "pkg-cli": pkg_cli_scenarios,
  "pkg-merging": pkg_merging_scenarios,
  "pkg-refs": pkg_refs_scenarios,
  "pkg-environment": pkg_environment_scenarios,
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
  chosen = chosen_scenarios()
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


def chosen_scenarios() -> list[str]:
  wanted = sys.argv[1:]
  return [n for n in SCENARIOS if not wanted or any(item in n for item in wanted)]


def run_forked(chosen: list[str]) -> int:
  """Run every scenario at once, each in a forked copy of this process.

  Everything is imported once, here; a fork starts with it already loaded, so a
  scenario costs only what it does. Scenarios own their NATS server, ports and fake
  Discord, so they do not interact, and separate processes keep the ones that edit
  the environment from leaking into the others.
  """
  started = time.perf_counter()
  logs: dict[str, str] = {}
  running: dict[int, str] = {}
  for name in chosen:
    log_file = tempfile.NamedTemporaryFile(prefix=f"smoke-{name}-", delete=False)  # noqa: SIM115
    log_file.close()
    logs[name] = log_file.name
    pid = os.fork()
    if pid == 0:
      code = 1
      try:
        fd = os.open(log_file.name, os.O_WRONLY | os.O_TRUNC)
        os.dup2(fd, 1)
        os.dup2(fd, 2)
        os.environ["SMOKE_CHILD"] = "1"
        sys.argv = [sys.argv[0], name]
        code = 1 if asyncio.run(main()) else 0
      except BaseException:
        traceback.print_exc()
      finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)  # a forked child never returns into the parent's code
    running[pid] = name
  took: dict[str, float] = {}
  codes: dict[str, int] = {}
  while running:
    pid, status = os.wait()
    name = running.pop(pid)
    took[name] = time.perf_counter() - started
    codes[name] = os.waitstatus_to_exitcode(status)
  passed = failed = 0
  for name in chosen:
    out = Path(logs[name]).read_text(errors="replace")
    Path(logs[name]).unlink(missing_ok=True)
    print(out, end="")
    for line in out.splitlines():
      if line.endswith(" failed") and " passed, " in line:
        counts = line.split()
        passed += int(counts[0])
        failed += int(counts[2])
    if codes[name] and not any(" passed, " in line for line in out.splitlines()):
      print(f"  FAIL  scenario {name} crashed (exit {codes[name]})")
      failed += 1
  print(f"\n{passed} passed, {failed} failed in {time.perf_counter() - started:.0f}s")
  print(
    "slowest:",
    ", ".join(
      f"{n} {t:.1f}s" for n, t in sorted(took.items(), key=lambda i: -i[1])[:14]
    ),
  )
  return failed


if __name__ == "__main__":
  if len(chosen_scenarios()) > 1 and not os.environ.get("SMOKE_CHILD"):
    sys.exit(run_forked(chosen_scenarios()))
  sys.exit(asyncio.run(main()))
