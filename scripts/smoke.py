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
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Self

sys.path.insert(0, str(Path(__file__).parent))

import hikari
from fake_discord import FakeDiscord
from nats.js.api import StorageType
from pydantic import BaseModel, JsonValue

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

    if guild_commands:
      guilded = Commands(service, guild_ids=guild_commands)

      @guilded.slash("guilded", description="Only in some guilds")
      async def only(ctx: Interaction) -> None:
        await ctx.respond("guilded")


def free_port() -> int:
  with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    return sock.getsockname()[1]


class Stack:
  """NATS, the fake Discord, and every Micro component, wired together."""

  def __init__(self, app: App, *, guilds: tuple[str, ...] = ("500",)) -> None:
    self.app = app
    self.guilds = guilds
    self.connection_events: list[dict[str, Any]] = []

  async def __aenter__(self) -> Self:
    self.fake = FakeDiscord(TOKEN, guilds=self.guilds)
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
    await asyncio.sleep(0.8)
    self.runtime = Runtime(
      f"nats://127.0.0.1:{port}", name="smoke", storage=StorageType.MEMORY
    )
    await self.runtime.__aenter__()

    async def note(message: Any) -> None:
      self.connection_events.append(json.loads(message.data))

    await self.runtime.nats.subscribe("micro.gateway.connection.>", cb=note)
    intents = hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT
    self.sync = CommandSync()
    await self.runtime.add(
      DiscordHTTPWorker(TOKEN, api_url=api),
      GatewayWorker(TOKEN, api_url=api, intents=intents, shard_count=1),
      InteractionRouter(),
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

      code, out = await cli(d, "worker")
      check(
        "a worker with nothing to host says so",
        code == 1 and "Nothing to host" in out,
        (code, out),
      )
      solo = await long_running(
        d, "worker", "--config", "micro.toml", "--process", "app"
      )
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
  code, out = await cli(here, "--help")
  check(
    "the help is grouped",
    all(f"{title}:" in out for title in ("Project", "Run", "Discord")),
    out[:300],
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
    await asyncio.sleep(0.5)
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
      await asyncio.sleep(12)  # idle long enough for every consumer's fetch to cycle
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


SCENARIOS: dict[str, Callable[[], Awaitable[None]]] = {
  "basics": basics,
  "sync": sync_scenarios,
  "cli": cli_scenarios,
  "pkg": pkg_scenarios,
  "service": service_scenarios,
  "routes": route_scenarios,
  "health": health_scenarios,
}


async def main() -> int:
  wanted = sys.argv[1:]
  for name, scenario in SCENARIOS.items():
    if not wanted or any(item in name for item in wanted):
      await scenario()
  failed = [name for name, ok in results if not ok]
  print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
  return len(failed)


if __name__ == "__main__":
  sys.exit(asyncio.run(main()))
