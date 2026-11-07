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


async def pkg_scenarios() -> None:
  print("pkg: packages, and upgrading them")
  from micro.scaffold import Project, packages

  with tempfile.TemporaryDirectory() as raw:
    d = Path(raw)
    code, out = await _micro(d, "init")
    check(
      "init adds hello as a tracked package",
      code == 0
      and (d / "services/hello/__init__.py").is_file()
      and "[hello]" in (d / "micro.lock").read_text(),
      out,
    )
    code, out = await _micro(d, "pkg", "list")
    check(
      "pkg list shows what ships and what you have",
      code == 0 and "chat" in out and "service" in out and "services/hello" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "add", "chat")
    check(
      "pkg add copies a package in",
      code == 0 and (d / "services/chat/schemas.py").is_file(),
      out,
    )
    code, out = await _micro(d, "pkg", "add", "service", "tickets")
    check(
      "a template takes a name",
      code == 0
      and 'Service("tickets")' in (d / "services/tickets/__init__.py").read_text(),
      out,
    )
    code, out = await _micro(d, "services", "add", "orders")
    check(
      "services add makes a blank service",
      code == 0
      and 'Service("orders")' in (d / "services/orders/__init__.py").read_text(),
      out,
    )
    (d / "services/mine").mkdir()
    (d / "services/mine/__init__.py").write_text("")
    code, out = await _micro(d, "services", "list")
    check(
      "services list says which came from a package and which are yours",
      code == 0
      and "hello" in out
      and "from hello (builtin)" in out
      and "orders" in out
      and "yours" in out
      and "mine" in out
      and "tickets" in out,
      out,
    )
    code, out = await _micro(d, "services", "add", "Bad Name")
    check("services add checks the name", code == 1 and "lowercase" in out, out)
    code, out = await _micro(d, "pkg", "add", "service")
    check(
      "a template without a name says so",
      code == 1 and "give the copy a name" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "add", "chat")
    check("adding twice refuses", code == 1 and "already exists" in out, out)
    code, out = await _micro(d, "pkg", "add", "nope")
    check(
      "an unknown package lists the choices",
      code == 1 and "No package" in out and "chat" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "status")
    check(
      "status: nothing changed, everything up to date",
      code == 0 and out.count("up to date") == 4,
      out,
    )

    chat = d / "services/chat/__init__.py"
    chat.write_text(chat.read_text() + "# my note\n")
    code, out = await _micro(d, "pkg", "status", "chat")
    check("status notices your edit", "edited by you" in out, out)
    code, out = await _micro(d, "pkg", "diff", "chat")
    check(
      "diff shows your edit against what Micro ships",
      "-# my note" in out and "(yours)" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "upgrade", "chat")
    check(
      "upgrade leaves your edit alone",
      code == 0 and chat.read_text().endswith("# my note\n"),
      out,
    )

    # Micro changed a file you never touched: what you were given differs from what ships now.
    project = Project(d, d.name, d / "services", "services.*")
    code, _ = await _micro(d, "pkg", "add", "ticker")
    ticker = d / "services/ticker/__init__.py"
    shipped = ticker.read_bytes()
    ticker.write_bytes(b"# an older Micro shipped this\n")
    lock = packages.Lock.load(project)
    lock.entries["ticker"].files["__init__.py"] = packages._hash(ticker.read_bytes())
    lock.save()
    code, out = await _micro(d, "pkg", "status", "ticker")
    check(
      "status offers an upgrade for a file you never touched",
      "upgrade available" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "upgrade", "ticker")
    check(
      "upgrade replaces it with what Micro ships now",
      code == 0 and ticker.read_bytes() == shipped,
      out,
    )

    code, out = await _micro(d, "pkg", "forget", "tickets")
    check(
      "forget stops tracking but keeps the files",
      code == 0
      and "[tickets]" not in (d / "micro.lock").read_text()
      and (d / "services/tickets/__init__.py").is_file(),
      out,
    )
    code, out = await _micro(d, "pkg", "status", "tickets")
    check(
      "an untracked name is an error", code == 1 and "Not an added package" in out, out
    )

  # Every outcome, one file each, against a source we control ("the next Micro").
  def build(root: Path, version: int) -> None:
    pkg = root / "demo"
    pkg.mkdir(parents=True, exist_ok=True)
    for name in (
      "__init__",
      "edited",
      "both",
      "deleted",
      "gone",
      "same",
      "dropped",
      "orphan",
    ):
      (pkg / f"{name}.py").write_text(f"v = 1  # {name}\n")
    if version == 2:
      for name in ("__init__", "both", "gone", "same"):
        (pkg / f"{name}.py").write_text(f"v = 2  # {name}\n")
      (pkg / "dropped.py").unlink()
      (pkg / "orphan.py").unlink()
      (pkg / "extra.py").write_text("v = 2  # extra\n")

  def prepare(root: Path) -> tuple[Project, Path]:
    source = root / "source"
    build(source, 1)
    project_dir = root / "project"
    (project_dir / "services").mkdir(parents=True)
    project = Project(project_dir, "p", project_dir / "services", "services.*")
    packages.add("demo", project, source=str(source))
    folder = project_dir / "services/demo"
    (folder / "edited.py").write_text("v = 99  # edited\n")
    (folder / "both.py").write_text("v = 99  # both\n")
    (folder / "deleted.py").unlink()
    (folder / "gone.py").unlink()
    (folder / "same.py").write_text("v = 2  # same\n")
    (folder / "orphan.py").write_text("v = 99  # orphan\n")
    shutil.rmtree(source)
    build(source, 2)  # the next Micro
    return project, folder

  with tempfile.TemporaryDirectory() as raw:
    project, folder = prepare(Path(raw))
    kinds = {c.file: c.kind for c in packages.status(project)[0].changes}
    want = {
      "__init__.py": "upgrade",
      "edited.py": "modified",
      "both.py": "conflict",
      "deleted.py": "deleted",
      "gone.py": "gone",
      "same.py": "refresh",
      "dropped.py": "remove",
      "orphan.py": "orphan",
      "extra.py": "add",
    }
    check(
      "status classifies each file",
      kinds == want,
      {k: (kinds.get(k), v) for k, v in want.items() if kinds.get(k) != v},
    )
    reports = packages.upgrade(project)
    text = lambda name: (
      (folder / name).read_text() if (folder / name).exists() else None
    )
    check(
      "upgrade: untouched file replaced, new file added",
      text("__init__.py") == "v = 2  # __init__\n"
      and text("extra.py") == "v = 2  # extra\n",
    )
    check(
      "upgrade: file Micro dropped is removed, edited one kept",
      text("dropped.py") is None and text("orphan.py") == "v = 99  # orphan\n",
    )
    check(
      "upgrade: your edits and deletions are untouched",
      text("edited.py") == "v = 99  # edited\n" and text("deleted.py") is None,
    )
    check(
      "upgrade: a conflict is left alone and reported",
      text("both.py") == "v = 99  # both\n"
      and text("gone.py") is None
      and len(reports[0].attention) == 2,
      reports[0].attention,
    )
    lock = packages.Lock.load(project).entries["demo"].files
    check(
      "the lock tracks what you were given, not what you edited",
      lock["both.py"] != packages._hash(b"v = 2  # both\n")
      and "orphan.py" not in lock
      and lock["__init__.py"] == packages._hash(b"v = 2  # __init__\n"),
    )
    patch = packages.diff(project, "demo")
    check(
      "diff shows a conflict's two sides",
      "-v = 99  # both" in patch and "+v = 2  # both" in patch,
      patch[:200],
    )

  with tempfile.TemporaryDirectory() as raw:
    project, folder = prepare(Path(raw))
    packages.upgrade(project, settle="theirs")
    check(
      "--theirs takes Micro's file and recreates a deleted one",
      (folder / "both.py").read_text() == "v = 2  # both\n"
      and (folder / "gone.py").read_text() == "v = 2  # gone\n",
    )
    check(
      "--theirs leaves nothing to decide",
      not any(r.attention for r in packages.status(project)),
    )

  with tempfile.TemporaryDirectory() as raw:
    project, folder = prepare(Path(raw))
    packages.upgrade(project, settle="mine")
    check(
      "--mine keeps your file and your deletion",
      (folder / "both.py").read_text() == "v = 99  # both\n"
      and not (folder / "gone.py").exists(),
    )
    after = {c.file: c.kind for c in packages.status(project)[0].changes}
    check(
      "--mine marks Micro's version reviewed: no conflict until it changes again",
      after["both.py"] == "modified" and after["gone.py"] == "deleted",
      after,
    )

  # A source is a folder of packages; micro.toml can name it.
  with tempfile.TemporaryDirectory() as raw:
    d = Path(raw)
    team = d / "team-packages"
    (team / "billing").mkdir(parents=True)
    (team / "billing/__init__.py").write_text('"""Invoices for the team."""\nv = 1\n')
    code, out = await _micro(d, "init")
    (d / "micro.toml").write_text(
      (d / "micro.toml").read_text() + '\n[sources]\nteam = "team-packages"\n'
    )
    code, out = await _micro(d, "pkg", "list")
    check(
      "pkg list shows each source on its own",
      code == 0
      and "builtin" in out
      and "team" in out
      and "billing" in out
      and "Invoices for the team" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "add", "billing")
    check(
      "a package is looked up in the builtin source by default",
      code == 1 and "builtin source" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "add", "billing", "--source", "team")
    check(
      "--source picks another source by name",
      code == 0 and (d / "services/billing/__init__.py").is_file(),
      out,
    )
    check(
      "the lock records where it came from",
      'source = "team"' in (d / "micro.lock").read_text(),
    )
    (team / "billing/__init__.py").write_text('"""Invoices for the team."""\nv = 2\n')
    code, out = await _micro(d, "pkg", "status", "billing")
    check(
      "status compares against the package's own source",
      "upgrade available" in out and "(team)" in out,
      out,
    )
    code, out = await _micro(d, "pkg", "upgrade", "billing")
    check(
      "upgrade takes the new version from that source",
      code == 0 and "v = 2" in (d / "services/billing/__init__.py").read_text(),
      out,
    )
    code, out = await _micro(
      d, "pkg", "add", "billing", "invoices", "--source", str(team)
    )
    check(
      "a folder path works as a source too",
      code == 0 and (d / "services/invoices/__init__.py").is_file(),
      out,
    )
    code, out = await _micro(d, "pkg", "add", "billing", "--source", "nowhere")
    check(
      "an unknown source name says what to do", code == 1 and "[sources]" in out, out
    )
    shutil.rmtree(team)
    code, out = await _micro(d, "pkg", "status", "billing")
    check(
      "a missing source folder is reported, not a crash",
      code == 0 and "can't compare" in out and "not a folder" in out,
      out,
    )
    code, out = await _micro(d, "dev", "--help")
    check("micro.toml with [sources] is still a valid deployment file", code == 0, out)


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


SCENARIOS: dict[str, Callable[[], Awaitable[None]]] = {
  "basics": basics,
  "sync": sync_scenarios,
  "cli": cli_scenarios,
  "pkg": pkg_scenarios,
  "service": service_scenarios,
  "routes": route_scenarios,
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
