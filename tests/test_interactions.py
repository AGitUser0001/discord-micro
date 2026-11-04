import asyncio
import itertools
import json
import time
from collections import Counter
from collections.abc import Callable
from typing import Annotated, Any, Literal

import httpx2
import pytest
from pydantic import BaseModel
from test_gateway import SESSIONS, FakeShard, eventually

from micro.discord import DiscordHTTPClient, DiscordHTTPWorker
from micro.discord.filters import (
  all_of,
  content_startswith,
  ignore_bots,
  in_channel,
  not_from,
)
from micro.discord.interactions import (
  Commands,
  CommandSync,
  Components,
  CustomId,
  Interaction,
  InteractionExpired,
  InteractionRouter,
  Modals,
  Option,
)
from micro.discord.interactions._commands import parse_options
from micro.discord.messages import reply_to
from micro.discord.objects import Channel, Member, PermissionOverwrite, Role, User
from micro.discord.state import ALL_PERMISSIONS, DiscordState, compute_permissions
from micro.discord.ui import (
  AllowedMentions,
  Button,
  Modal,
  Select,
  TextInput,
  embed,
  message_body,
)
from micro.gateway import GatewayWorker
from micro.runtime import Runtime
from micro.schemas import events
from micro.service import Service

_IDS = itertools.count(1000)


class FakeDiscord:
  """Records API calls and answers them like Discord would."""

  def __init__(self) -> None:
    self.calls: list[tuple[str, str, Any]] = []

  def __call__(self, request: httpx2.Request) -> httpx2.Response:
    body = json.loads(request.content) if request.content else None
    self.calls.append((request.method, request.url.path, body))
    path = request.url.path
    if path == "/applications/@me":
      return httpx2.Response(200, json={"id": "999", "name": "bot"})
    if path.endswith("/callback"):
      return httpx2.Response(204)
    if request.method == "PUT" and "/commands" in path:
      return httpx2.Response(200, json=body)
    if path.startswith("/webhooks/") or path.endswith("/messages"):
      return httpx2.Response(200, json={"id": "5", "channel_id": "10", "content": ""})
    if path == "/guilds/1":
      return httpx2.Response(
        200,
        json={
          "id": "1",
          "name": "g",
          "owner_id": "2",
          "roles": [{"id": "1", "name": "@everyone", "permissions": "1024"}],
        },
      )
    if path == "/guilds/1/members/3":
      return httpx2.Response(
        200, json={"user": {"id": "3", "username": "u"}, "roles": []}
      )
    return httpx2.Response(404, json={"message": "unknown"})

  def matching(self, method: str, predicate: Callable[[str], bool]) -> list[Any]:
    return [body for m, path, body in self.calls if m == method and predicate(path)]


def interaction(kind: int, data: dict[str, Any], **extra: Any) -> dict[str, Any]:
  return {
    "id": str(next(_IDS)),
    "token": "tok",
    "application_id": "999",
    "type": kind,
    "data": data,
    "guild_id": "1",
    "channel_id": "10",
    "member": {"user": {"id": "3", "username": "ada"}, "roles": []},
    **extra,
  }


async def start(
  nats_url: str, discord: FakeDiscord, *services: Service, sync: bool = True
) -> tuple[Runtime, CommandSync]:
  SESSIONS.clear()
  gateway = GatewayWorker(
    "t", intents=0, lease_ttl=3, max_concurrency=16, session_factory=FakeShard
  )
  http = DiscordHTTPWorker(
    "t", transport=httpx2.MockTransport(discord), api_url="https://d.test"
  )
  syncer = CommandSync()
  runtime = Runtime(nats_url)
  await runtime.add(http, InteractionRouter(), *services, gateway)
  if sync:
    await runtime.add(syncer)
    await asyncio.wait_for(syncer.synced.wait(), 10)
  await eventually(lambda: gateway.publishing_shards == (0,))
  names = {service.name for service in services}
  await runtime.directory.wait_for(
    lambda d: names <= {e.name for e in d.entries("service")}
  )
  return runtime, syncer


async def dispatch(payload: dict[str, Any]) -> None:
  await SESSIONS[0].dispatch("INTERACTION_CREATE", payload)


async def stop(runtime: Runtime) -> None:
  await runtime.drain()
  await runtime.close()


def callbacks(discord: FakeDiscord) -> list[Any]:
  return discord.matching("POST", lambda path: path.endswith("/callback"))


def test_commands_route_typed_options_to_their_service(nats_url: str) -> None:
  discord = FakeDiscord()
  tickets, other = Service("tickets"), Service("other")
  ticket_commands, other_commands = Commands(tickets), Commands(other)
  seen: dict[str, Any] = {}

  @ticket_commands.slash("ticket", description="Open a ticket")
  async def ticket(
    ctx: Interaction,
    topic: Annotated[str, Option("What about")],
    urgent: bool = False,
    level: Literal["low", "high"] = "low",
    who: User | None = None,
  ) -> None:
    seen.update(topic=topic, urgent=urgent, level=level, who=who, at=time.monotonic())
    await ctx.reply(f"Opened {topic} for <@{ctx.user.id}>")

  @other_commands.slash("ping")
  async def ping(ctx: Interaction) -> None:
    seen["pinged"] = True

  async def exercise() -> None:
    runtime, _ = await start(nats_url, discord, tickets, other)
    try:
      sent = time.monotonic()
      await dispatch(
        interaction(
          2,
          {
            "type": 1,
            "name": "ticket",
            "options": [
              {"name": "topic", "type": 3, "value": "printer"},
              {"name": "urgent", "type": 5, "value": True},
              {"name": "who", "type": 6, "value": "4"},
            ],
            "resolved": {"users": {"4": {"id": "4", "username": "bob"}}},
          },
        )
      )
      await eventually(lambda: bool(callbacks(discord)))
      assert seen["at"] - sent < 1.0, (
        "routing must leave room for Discord's 3s deadline"
      )
      assert (seen["topic"], seen["urgent"], seen["level"]) == ("printer", True, "low")
      assert seen["who"] == User(id="4", username="bob")
      assert "pinged" not in seen
      (reply,) = callbacks(discord)
      assert (reply["type"], reply["data"]["content"]) == (4, "Opened printer for <@3>")
      assert reply["data"]["allowed_mentions"]["parse"] == []

      await dispatch(interaction(2, {"type": 1, "name": "nope"}))
      await eventually(lambda: len(callbacks(discord)) == 2)
      assert callbacks(discord)[1]["data"]["flags"] == 64  # router: nobody handles it
    finally:
      await stop(runtime)

  asyncio.run(exercise())


def test_replicas_share_a_route_and_each_interaction_runs_once(nats_url: str) -> None:
  discord = FakeDiscord()
  handled: Counter[str] = Counter()

  def replica(tag: str) -> Service:
    service = Service("scaled")
    commands = Commands(service)

    @commands.slash("work")
    async def work(ctx: Interaction) -> None:
      handled[tag] += 1
      await ctx.reply("ok")

    return service

  async def exercise() -> None:
    runtime, _ = await start(nats_url, discord, replica("a"))
    extra = Runtime(nats_url)
    await extra.add(replica("b"), replica("c"))
    try:
      for _ in range(30):
        await dispatch(interaction(2, {"type": 1, "name": "work"}))
      await eventually(lambda: sum(handled.values()) == 30)
      await asyncio.sleep(0.3)
      assert sum(handled.values()) == 30 and len(handled) > 1
      duplicate = interaction(2, {"type": 1, "name": "work"})
      await dispatch(duplicate)
      await dispatch(duplicate)  # A redelivered dispatch is deduplicated.
      await eventually(lambda: sum(handled.values()) == 31)
      await asyncio.sleep(0.3)
      assert sum(handled.values()) == 31
    finally:
      await stop(extra)
      await stop(runtime)

  asyncio.run(exercise())


def test_slow_handlers_are_deferred_then_filled_in(nats_url: str) -> None:
  discord = FakeDiscord()
  service = Service("slow")
  commands = Commands(service, defer_after=0.2)

  @commands.slash("report", ephemeral_defer=True)
  async def report(ctx: Interaction) -> None:
    await asyncio.sleep(0.6)
    await ctx.reply("done")
    await ctx.followup("and more", ephemeral=True)

  async def exercise() -> None:
    runtime, _ = await start(nats_url, discord, service)
    try:
      await dispatch(interaction(2, {"type": 1, "name": "report"}))
      await eventually(
        lambda: bool(discord.matching("POST", lambda p: p.startswith("/webhooks/")))
      )
      assert callbacks(discord) == [{"type": 5, "data": {"flags": 64}}]
      (edit,) = discord.matching("PATCH", lambda p: p.endswith("/messages/@original"))
      assert edit["content"] == "done"
      (followup,) = discord.matching("POST", lambda p: p.startswith("/webhooks/"))
      assert followup["flags"] == 64
    finally:
      await stop(runtime)

  asyncio.run(exercise())


class Vote(BaseModel):
  poll: int
  choice: str


VOTE = CustomId("poll.vote", Vote)
FEEDBACK = CustomId("feedback")


def test_components_modals_autocomplete_errors_and_hooks(nats_url: str) -> None:
  discord = FakeDiscord()
  service = Service("ui")
  commands = Commands(service)
  modals = Modals(service)
  votes: list[Vote] = []
  feedback: list[dict[str, str]] = []
  audit: list[str] = []

  class AuditedComponents(Components):
    async def around(self, ctx: Interaction, call: Any) -> None:
      audit.append(ctx.custom_id or "")
      await call()

  components = AuditedComponents(service)

  @components.on(VOTE)
  async def vote(ctx: Interaction, state: Vote) -> None:
    votes.append(state)
    await ctx.update("Thanks!", components=[])

  @modals.on(FEEDBACK)
  async def submitted(ctx: Interaction) -> None:
    feedback.append(ctx.fields)
    await ctx.reply("Noted", ephemeral=True)

  @commands.slash("feedback")
  async def ask(ctx: Interaction) -> None:
    await ctx.modal(Modal(FEEDBACK.encode(), "Feedback", [TextInput("text", "Say it")]))

  @commands.slash("fruit")
  async def fruit(ctx: Interaction, name: str) -> None:
    raise RuntimeError("boom")

  @fruit.autocomplete("name")
  async def suggest(ctx: Interaction, value: str) -> list[str]:
    return [f for f in ("apple", "apricot", "banana") if f.startswith(value)]

  async def exercise() -> None:
    runtime, _ = await start(nats_url, discord, service)
    try:
      custom = VOTE.encode(Vote(poll=7, choice="yes"))
      await dispatch(interaction(3, {"custom_id": custom, "component_type": 2}))
      await dispatch(interaction(2, {"type": 1, "name": "feedback"}))
      row = {
        "type": 1,
        "components": [{"type": 4, "custom_id": "text", "value": "great"}],
      }
      await dispatch(
        interaction(5, {"custom_id": FEEDBACK.encode(), "components": [row]})
      )
      focused = {"name": "name", "type": 3, "value": "ap", "focused": True}
      await dispatch(interaction(4, {"type": 1, "name": "fruit", "options": [focused]}))
      option = {"name": "name", "type": 3, "value": "x"}
      await dispatch(interaction(2, {"type": 1, "name": "fruit", "options": [option]}))
      await eventually(lambda: len(callbacks(discord)) == 5)
      by_type: dict[int, list[Any]] = {}
      for body in callbacks(discord):
        by_type.setdefault(body["type"], []).append(body)
      assert votes == [Vote(poll=7, choice="yes")] and audit == [custom]
      assert by_type[7][0]["data"]["content"] == "Thanks!"
      assert by_type[9][0]["data"]["custom_id"] == "feedback"
      assert feedback == [{"text": "great"}]
      assert [c["value"] for c in by_type[8][0]["data"]["choices"]] == [
        "apple",
        "apricot",
      ]
      errors = [
        b for b in by_type[4] if b["data"]["content"] == "Something went wrong."
      ]
      assert errors and errors[0]["data"]["flags"] == 64
    finally:
      await stop(runtime)

  asyncio.run(exercise())


def test_command_sync_registers_scopes_once(nats_url: str) -> None:
  discord = FakeDiscord()

  def make() -> Service:
    service = Service("cmds")
    commands = Commands(service)

    @commands.slash("hello", description="Say hi")
    async def hello(ctx: Interaction) -> None: ...

    @commands.slash("local", guild_ids=[42])
    async def local(ctx: Interaction) -> None: ...

    return service

  def puts() -> list[tuple[str, Any]]:
    return [(p, b) for m, p, b in discord.calls if m == "PUT"]

  async def exercise() -> None:
    runtime, syncer = await start(nats_url, discord, make(), make(), sync=False)
    try:
      await runtime.add(syncer, CommandSync("second-sync"))
      await eventually(lambda: len(puts()) == 2)
      await asyncio.sleep(0.5)
      assert sorted(p for p, _ in puts()) == [
        "/applications/999/commands",
        "/applications/999/guilds/42/commands",
      ]
      (global_body,) = [b for p, b in puts() if p == "/applications/999/commands"]
      assert [c["name"] for c in global_body] == ["hello"]
    finally:
      await stop(runtime)

  asyncio.run(exercise())


def test_filters_messages_and_state(nats_url: str) -> None:
  discord = FakeDiscord()
  service = Service("chat")
  seen: list[str] = []

  @service.listen(
    events.MESSAGE_CREATE,
    when=all_of(ignore_bots, not_from(999), in_channel(10), content_startswith("!")),
  )
  async def command(message: Any) -> None:
    seen.append(message.content)
    await reply_to(
      DiscordHTTPClient(service.runtime),
      message,
      "ok",
      embeds=[embed("T", fields=[("a", "b")])],
    )

  def message(content: str, author: dict[str, Any]) -> dict[str, Any]:
    return {
      "id": "1",
      "channel_id": "10",
      "guild_id": "1",
      "content": content,
      "author": {
        "username": "x",
        "discriminator": "0",
        "avatar": None,
        "global_name": None,
        **author,
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

  async def exercise() -> None:
    runtime, _ = await start(nats_url, discord, service, sync=False)
    try:
      shard = SESSIONS[0]
      for content, author in (
        ("!a", {"id": "3"}),
        ("!bot", {"id": "4", "bot": True}),
        ("!self", {"id": "999"}),
        ("plain", {"id": "3"}),
      ):
        await shard.dispatch("MESSAGE_CREATE", message(content, author))
      await eventually(
        lambda: bool(discord.matching("POST", lambda p: p == "/channels/10/messages"))
      )
      await asyncio.sleep(0.3)
      assert seen == ["!a"]
      (sent,) = discord.matching("POST", lambda p: p == "/channels/10/messages")
      assert sent["message_reference"]["message_id"] == "1"
      assert sent["embeds"][0]["fields"] == [
        {"name": "a", "value": "b", "inline": False}
      ]
      state = DiscordState(runtime)
      read = await state.guild(1)
      assert (read.source, read.value.name) == ("http", "g")
      permissions = await state.permissions(1, 3)
      assert (permissions.source, permissions.value) == ("http", 1024)
    finally:
      await stop(runtime)

  asyncio.run(exercise())


def test_custom_ids_are_compact_typed_and_version_tolerant() -> None:
  encoded = VOTE.encode(Vote(poll=7, choice="yes"))
  assert encoded == 'poll.vote:[7,"yes"]'
  assert VOTE.decode(encoded) == Vote(poll=7, choice="yes")
  with pytest.raises(ValueError, match="100"):
    VOTE.encode(Vote(poll=1, choice="x" * 120))
  with pytest.raises(ValueError):
    VOTE.decode('other:[1,"a"]')
  assert FEEDBACK.encode() == "feedback" and FEEDBACK.decode("feedback") is None

  class VoteV2(BaseModel):  # Appended optional field: old buttons still decode.
    poll: int
    choice: str
    weight: int = 1

  v2 = CustomId("poll.vote", VoteV2)
  assert v2.decode(encoded) == VoteV2(poll=7, choice="yes", weight=1)
  assert VOTE.decode(v2.encode(VoteV2(poll=7, choice="yes", weight=3))) == Vote(
    poll=7, choice="yes"
  )


def test_options_builders_and_permissions() -> None:
  async def handler(
    ctx: Interaction,
    count: Annotated[int, Option("How many", min_value=1)],
    mode: Literal["a", "b"] = "a",
    role: Role | None = None,
  ) -> None: ...

  specs = [spec.to_dict() for spec in parse_options(handler)]
  assert specs[0] == {
    "type": 4,
    "name": "count",
    "description": "How many",
    "required": True,
    "min_value": 1,
  }
  assert specs[1]["choices"] == [
    {"name": "a", "value": "a"},
    {"name": "b", "value": "b"},
  ]
  assert specs[2]["type"] == 8 and not specs[2]["required"]

  assert message_body("hi")["allowed_mentions"] == {"parse": [], "replied_user": False}
  assert AllowedMentions.only(users=[5]).to_dict()["users"] == ["5"]
  body = message_body(
    components=[
      Button("A", custom_id="a"),
      Button("B", url="https://x"),
      Select("s", ["x"]),
    ]
  )
  assert [len(row["components"]) for row in body["components"]] == [2, 1]

  roles = [Role(id="1", permissions="1024"), Role(id="9", permissions=str(1 << 11))]
  member = Member(user=User(id="3"), roles=["9"])
  assert compute_permissions("1", "2", roles, member, "3") == 1024 | (1 << 11)
  assert compute_permissions("1", "3", roles, member, "3") == ALL_PERMISSIONS
  channel = Channel(
    id="10",
    permission_overwrites=[
      PermissionOverwrite(id="1", type=0, deny="1024"),
      PermissionOverwrite(id="3", type=1, allow="1024"),
    ],
  )
  assert compute_permissions("1", "2", roles, member, "3", channel) == 1024 | (1 << 11)


def test_expired_interactions_fail_clearly() -> None:
  ctx = Interaction(
    interaction(2, {"type": 1, "name": "x"}),
    DiscordHTTPClient(None),  # type: ignore[arg-type]
    received=time.monotonic() - 16 * 60,
  )
  with pytest.raises(InteractionExpired):
    asyncio.run(ctx.reply("late"))
