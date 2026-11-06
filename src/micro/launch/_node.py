import asyncio
import json
import logging
import os
import re
import signal
import socket
import sys
import time
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nats.aio.msg import Msg
from nats.errors import NoServersError
from pydantic import JsonValue

from micro import subjects
from micro.runtime import RUNTIME_KIND, Runtime

from ._config import DeploymentConfig
from ._server import reachable

logger = logging.getLogger("micro.node")

NODE_KIND = "node"
"""Presence kind of a node: `name` is the node, `metadata` its deployment and groups."""

_RESTART_DELAY = 1.0
_RESTART_DELAY_LIMIT = 30.0
_STABLE_AFTER = 60.0


@dataclass(eq=False)
class Child:
  group: str
  process: asyncio.subprocess.Process
  started: float = field(default_factory=time.monotonic)
  retiring: bool = False

  @property
  def pid(self) -> int:
    return self.process.pid


def default_node_name() -> str:
  """This machine's hostname, trimmed to what a subject token allows."""
  host = socket.gethostname().split(".")[0]
  return re.sub(r"[^A-Za-z0-9_-]", "-", host).strip("-") or "node"


class Node:
  """One machine's share of a deployment, from `micro.toml`.

  A node connects to a NATS server that is already running (`micro server start`),
  runs every process group with its replicas, restarts crashed processes, and
  answers `micro nodes list`, `micro dev scale`, and `micro dev roll` over NATS. Several nodes, each with
  its own name, can serve the same deployment. Stopping a node drains every
  process it started and leaves the server alone.
  """

  def __init__(
    self, config: DeploymentConfig, path: str | Path, name: str | None = None
  ) -> None:
    self.config = config
    self.path = Path(path).resolve()
    self.root = self.path.parent
    self.name = subjects.token(name or default_node_name())
    self.desired = {name: group.replicas for name, group in config.processes.items()}
    self.children: dict[str, list[Child]] = {name: [] for name in config.processes}
    self._runtime: Runtime | None = None
    self._stopping = False
    self._delays: dict[str, float] = {}
    self._monitors: set[asyncio.Task[None]] = set()

  async def run(self) -> None:
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def interrupt() -> None:
      if stop.is_set():
        self._hurry()
      stop.set()

    # The children and nats-server run in their own sessions (see `_spawn`), so a
    # terminal's Ctrl-C or hangup reaches only this process, which then stops
    # everything in order: children drain, then NATS goes last.
    signals = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, "SIGHUP"):
      signals.append(signal.SIGHUP)
    for sig in signals:
      with suppress(NotImplementedError, RuntimeError):
        loop.add_signal_handler(sig, interrupt)
    try:
      local = self.config.local_nats()
      if local is not None and not await reachable(*local):
        raise ConnectionError(self._missing_server())
      runtime = Runtime(
        self.config.nats,
        name=f"{self.config.name}.node",
        replicas=self.config.jetstream_replicas,
      )
      self._runtime = runtime
      try:
        await runtime.start()
      except (NoServersError, OSError, TimeoutError) as error:
        raise ConnectionError(self._missing_server()) from error
      taken = any(
        entry.name == self.name and entry.metadata.get("deployment") == self.config.name
        for entry in runtime.directory.entries(NODE_KIND)
      )
      if taken:
        raise ValueError(
          f"A node named {self.name!r} is already running for {self.config.name!r}; "
          "pick another with --name."
        )
      groups: list[JsonValue] = [*sorted(self.config.processes)]
      await runtime.register(
        kind=NODE_KIND,
        name=self.name,
        id=runtime.instance,
        metadata={"deployment": self.config.name, "processes": groups},
      )
      for operation, handler in (
        ("scale", self._on_scale),
        ("roll", self._on_roll),
        ("ps", self._on_ps),
      ):
        await runtime.nats.subscribe(
          subjects.node(self.config.name, self.name, operation), cb=handler
        )
      for group, replicas in self.desired.items():
        for _ in range(replicas):
          await self._spawn(group)
      logger.info("Node %s of %s is up", self.name, self.config.name)
      await stop.wait()
    finally:
      await self.shutdown()

  def _missing_server(self) -> str:
    return (
      f"No NATS server at {', '.join(self.config.nats)}. Start one with "
      "`micro server start` on the machine it names."
    )

  def _hurry(self) -> None:
    """A second Ctrl-C: a child's second signal makes it skip the rest of its drain."""
    for group in self.children.values():
      for child in group:
        with suppress(ProcessLookupError):
          child.process.send_signal(signal.SIGTERM)

  async def shutdown(self) -> None:
    self._stopping = True
    children = [child for group in self.children.values() for child in group]
    for child in children:
      child.retiring = True
      with suppress(ProcessLookupError):
        child.process.send_signal(signal.SIGTERM)
    await asyncio.gather(*(child.process.wait() for child in children))
    for task in tuple(self._monitors):
      task.cancel()
    if self._runtime is not None:
      await self._runtime.close()
      self._runtime = None

  # Processes -------------------------------------------------------------------

  async def _spawn(self, group: str) -> Child:
    settings = self.config.processes[group]
    env = os.environ | settings.env | {"MICRO_NATS_URL": ",".join(self.config.nats)}
    process = await asyncio.create_subprocess_exec(
      sys.executable,
      "-m",
      "micro",
      "worker",
      "--config",
      str(self.path),
      "--process",
      group,
      cwd=self.root,
      env=env,
      start_new_session=True,
    )
    child = Child(group, process)
    self.children[group].append(child)
    task = asyncio.create_task(self._monitor(child))
    self._monitors.add(task)
    task.add_done_callback(self._monitors.discard)
    logger.info("Started %s (pid %d)", group, process.pid)
    return child

  async def _monitor(self, child: Child) -> None:
    code = await child.process.wait()
    with suppress(ValueError):
      self.children[child.group].remove(child)
    if child.retiring or self._stopping:
      return
    lived = time.monotonic() - child.started
    delay = self._delays.get(child.group, _RESTART_DELAY)
    delay = _RESTART_DELAY if lived > _STABLE_AFTER else delay
    logger.warning(
      "%s (pid %d) exited with %s; restarting in %.0fs",
      child.group,
      child.pid,
      code,
      delay,
    )
    self._delays[child.group] = min(delay * 2, _RESTART_DELAY_LIMIT)
    await asyncio.sleep(delay)
    if (
      not self._stopping and len(self.children[child.group]) < self.desired[child.group]
    ):
      await self._spawn(child.group)

  async def _retire(self, child: Child) -> None:
    child.retiring = True
    with suppress(ProcessLookupError):
      child.process.send_signal(signal.SIGTERM)
    await child.process.wait()

  async def _wait_ready(self, child: Child) -> bool:
    """Wait until the child's runtime is registered, or it exits."""
    assert self._runtime is not None
    directory = self._runtime.directory

    def registered(_: object) -> bool:
      return any(
        entry.metadata.get("pid") == child.pid
        for entry in directory.entries(RUNTIME_KIND)
      )

    waiting = asyncio.create_task(directory.wait_for(registered))
    exited = asyncio.create_task(child.process.wait())
    await asyncio.wait((waiting, exited), return_when=asyncio.FIRST_COMPLETED)
    for task in (waiting, exited):
      task.cancel()
    return waiting.done() and not waiting.cancelled() and not exited.done()

  async def scale(self, group: str, replicas: int) -> None:
    if group not in self.desired:
      raise KeyError(group)
    if replicas < 0:
      raise ValueError("replicas cannot be negative.")
    self.desired[group] = replicas
    while len(self.children[group]) < replicas:
      await self._spawn(group)
    extra = sorted(self.children[group], key=lambda child: child.started)[replicas:]
    await asyncio.gather(*(self._retire(child) for child in extra))

  async def roll(self, group: str) -> None:
    """Replace each replica: start a new one, wait until ready, drain the old one."""
    if group not in self.desired:
      raise KeyError(group)
    for old in tuple(self.children[group]):
      new = await self._spawn(group)
      if not await self._wait_ready(new):
        raise RuntimeError(f"A new {group} process exited before becoming ready.")
      await self._retire(old)

  def processes(self) -> list[dict[str, Any]]:
    return [
      {
        "group": child.group,
        "pid": child.pid,
        "uptime": round(time.monotonic() - child.started),
      }
      for group in self.children.values()
      for child in group
    ]

  # Control ---------------------------------------------------------------------

  async def _reply(self, message: Msg, body: dict[str, Any]) -> None:
    if message.reply and self._runtime is not None:
      await self._runtime.nats.publish(message.reply, json.dumps(body).encode())

  async def _on_scale(self, message: Msg) -> None:
    try:
      request = json.loads(message.data)
      await self.scale(str(request["process"]), int(request["replicas"]))
      await self._reply(message, {"ok": True, "processes": self.processes()})
    except Exception as exc:
      await self._reply(message, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})

  async def _on_roll(self, message: Msg) -> None:
    try:
      request = json.loads(message.data)
      await self.roll(str(request["process"]))
      await self._reply(message, {"ok": True, "processes": self.processes()})
    except Exception as exc:
      await self._reply(message, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})

  async def _on_ps(self, message: Msg) -> None:
    await self._reply(
      message, {"ok": True, "desired": self.desired, "processes": self.processes()}
    )
