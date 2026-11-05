"""The `micro` command line."""

import argparse
import asyncio
import json
import logging
import math
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from micro import subjects
from micro.runtime import Runtime, event_loop_factory

DEFAULT_CONFIG = "micro.toml"


def main(argv: Sequence[str] | None = None) -> int:
  parser = _parser()
  args = parser.parse_args(argv)
  if getattr(args, "handler", None) is None:
    parser.print_help()
    return 0
  level = "DEBUG" if args.verbose else os.environ.get("MICRO_LOG_LEVEL", "INFO").upper()
  logging.basicConfig(
    level=level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
  )
  sys.path.insert(0, os.getcwd())
  try:
    with asyncio.Runner(loop_factory=event_loop_factory) as runner:
      return runner.run(args.handler(args)) or 0
  except KeyboardInterrupt:
    return 130
  except (FileExistsError, FileNotFoundError, ValueError) as error:
    print(f"micro: {error}", file=sys.stderr)
    return 1


def _version() -> str:
  from importlib.metadata import PackageNotFoundError, version

  try:
    return version("micro")
  except PackageNotFoundError:
    return "unknown"


def _parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(prog="micro", description=__doc__)
  parser.add_argument(
    "-v", "--version", action="version", version=f"micro {_version()}"
  )
  parser.add_argument(
    "-V", "--verbose", action="store_true", help="debug logging (any command)"
  )
  commands = parser.add_subparsers(metavar="command")

  help_command = commands.add_parser("help", help="show this help, or a command's")
  help_command.add_argument("topic", nargs="?", help="a command, e.g. up")

  def show_help(args: argparse.Namespace) -> int:
    if args.topic is None:
      parser.print_help()
    elif args.topic in commands.choices:
      commands.choices[args.topic].print_help()
    else:
      raise ValueError(f"No command {args.topic!r}; see `micro help`.")
    return 0

  async def help_handler(args: argparse.Namespace) -> int:
    return show_help(args)

  help_command.set_defaults(handler=help_handler)

  docs = commands.add_parser("docs", help="open the documentation in a browser")
  docs.add_argument("--no-browser", action="store_true", help="only print the address")
  docs.set_defaults(handler=_docs)

  init = commands.add_parser("init", help="add Micro to the project in this directory")
  init.set_defaults(handler=_init)

  add = commands.add_parser("add", help="add to the project")
  add_actions = add.add_subparsers(required=True, metavar="kind")
  add_service = add_actions.add_parser("service", help="a new service module")
  add_service.add_argument("name")
  add_service.set_defaults(handler=_add_service)
  add_example = add_actions.add_parser(
    "example", help="copy a bundled example (list without NAME)"
  )
  add_example.add_argument("name", nargs="?")
  add_example.set_defaults(handler=_add_example)

  run = commands.add_parser("run", help="host components in this process")
  run.add_argument("targets", nargs="*", help="module:attribute components to host")
  run.add_argument("--config", help="deployment file to read a process group from")
  run.add_argument("--process", help="process group in the deployment file")
  run.add_argument("--nats", help="NATS URL(s), comma separated")
  run.add_argument("--name", help="runtime name shown in presence")
  run.set_defaults(handler=_run)

  up = commands.add_parser("up", help="run a whole deployment on this machine")
  up.add_argument("config", nargs="?", default=DEFAULT_CONFIG)
  up.set_defaults(handler=_up)

  for name, help_text in (
    ("ps", "list a deployment's processes and live components"),
    ("scale", "change the replicas of a process group"),
    ("roll", "replace every replica of a process group, one at a time"),
  ):
    command = commands.add_parser(name, help=help_text)
    command.add_argument("--config", default=DEFAULT_CONFIG)
    if name != "ps":
      command.add_argument("process")
    if name == "scale":
      command.add_argument("replicas", type=int)
    command.set_defaults(handler=_control, operation=name)

  slash = commands.add_parser(
    "commands", help="inspect and sync Discord application commands"
  )
  slash.add_argument("--config", default=DEFAULT_CONFIG)
  slash_actions = slash.add_subparsers(required=True, metavar="action")
  slash_actions.add_parser(
    "list", help="commands, their state, and live versions"
  ).set_defaults(handler=_commands, action="list")
  slash_actions.add_parser("sync", help="sync changed scopes now").set_defaults(
    handler=_commands, action="sync"
  )
  forget = slash_actions.add_parser(
    "forget", help="drop a retired service's commands, then sync"
  )
  forget.add_argument("service")
  forget.set_defaults(handler=_commands, action="forget")

  gateway = commands.add_parser("gateway", help="operate the Discord Gateway")
  gateway.add_argument("--config", default=DEFAULT_CONFIG)
  actions = gateway.add_subparsers(required=True, metavar="action")
  actions.add_parser("status").set_defaults(handler=_gateway, action="status")
  shards = actions.add_parser("shards", help="roll in a generation with N shards")
  shards.add_argument("count", type=int)
  shards.set_defaults(handler=_gateway, action="shards")
  actions.add_parser("roll", help="replace every connection").set_defaults(
    handler=_gateway, action="roll"
  )
  presence = actions.add_parser("presence", help="set the bot presence")
  presence.add_argument("status", choices=("online", "idle", "dnd", "offline"))
  presence.add_argument("--activity")
  presence.set_defaults(handler=_gateway, action="presence")
  return parser


async def _docs(args: argparse.Namespace) -> int:
  from micro._docs import serve

  await asyncio.to_thread(serve, browser=not args.no_browser)
  return 0


async def _init(args: argparse.Namespace) -> int:
  from micro.scaffold import init

  project = init()
  services = project.services.relative_to(project.root)
  print(f"Added micro.toml and {services}/hello.py.\n\n  DISCORD_TOKEN=... micro up")
  return 0


async def _add_service(args: argparse.Namespace) -> int:
  from micro.scaffold import add_service

  path = add_service(args.name)
  print(f"Added {path.name}; `micro up` loads it with the other services.")
  return 0


async def _add_example(args: argparse.Namespace) -> int:
  from micro.scaffold import add_example, examples

  if args.name is None:
    for name, summary in examples().items():
      print(f"  {name:10s} {summary}")
    return 0
  for path in add_example(args.name):
    print(f"Added {path.name}")
  return 0


async def _run(args: argparse.Namespace) -> int:
  from micro.launch import load_components, load_config

  targets = list(args.targets)
  servers = args.nats.split(",") if args.nats else None
  name = args.name
  replicas = 1
  if args.config or args.process:
    if not (args.config and args.process):
      raise SystemExit("--config and --process are used together.")
    config = load_config(args.config)
    group = config.processes[args.process]
    targets.extend(group.components)
    servers = servers or (
      os.environ["MICRO_NATS_URL"].split(",")
      if "MICRO_NATS_URL" in os.environ
      else config.nats
    )
    name = name or f"{config.name}.{args.process}"
    replicas = config.jetstream_replicas
  if not targets:
    raise SystemExit("Nothing to run: pass module:attribute targets or --process.")
  components = load_components(targets)
  runtime = Runtime(servers, name=name or "micro", replicas=replicas)
  await runtime.serve(*components)
  return 0


async def _up(args: argparse.Namespace) -> int:
  from micro.launch import Supervisor, load_config

  path = Path(args.config)
  await Supervisor(load_config(path), path).run()
  return 0


def _deployment(path: str) -> tuple[str, list[str] | None]:
  from micro.launch import load_config

  if Path(path).exists():
    config = load_config(path)
    return config.name, config.nats
  return "micro", None


async def _control(args: argparse.Namespace) -> int:
  name, servers = _deployment(args.config)
  request: dict[str, Any] = {}
  if args.operation != "ps":
    request["process"] = args.process
  if args.operation == "scale":
    request["replicas"] = args.replicas
  async with Runtime(servers, name="micro.cli") as runtime:
    reply = await runtime.nats.request(
      subjects.supervisor(name, args.operation),
      json.dumps(request).encode(),
      # Rolling waits for each replacement to become ready, however long that is.
      timeout=math.inf if args.operation == "roll" else 30,
    )
    body = json.loads(reply.data)
    if args.operation == "ps":
      for entry in runtime.directory.entries():
        if entry.kind != "runtime":
          body.setdefault("components", []).append(
            {"kind": entry.kind, "name": entry.name, "runtime": entry.instance[:8]}
          )
  print(json.dumps(body, indent=2))
  return 0 if body.get("ok") else 1


async def _gateway(args: argparse.Namespace) -> int:
  from micro.gateway import ActivityUpdate, GatewayControl

  _, servers = _deployment(args.config)
  async with Runtime(servers, name="micro.cli") as runtime:
    control = GatewayControl(runtime)
    if args.action == "status":
      status = await control.status()
      print(
        json.dumps(
          {
            "desired": status.desired.model_dump() if status.desired else None,
            "active": status.active.model_dump() if status.active else None,
            "workers": [worker.id for worker in status.workers],
            "leases": {
              key: lease.model_dump() for key, lease in sorted(status.leases.items())
            },
          },
          indent=2,
        )
      )
    elif args.action == "shards":
      print((await control.set_shard_count(args.count)).model_dump_json())
    elif args.action == "roll":
      print((await control.roll()).model_dump_json())
    else:
      activity = ActivityUpdate(name=args.activity) if args.activity else None
      await control.update_presence(status=args.status, activity=activity)
  return 0


async def _commands(args: argparse.Namespace) -> int:
  from micro.coordination import Declarations
  from micro.discord import DiscordHTTPClient
  from micro.discord.interactions import SYNC_LOCK, sync_commands

  _, servers = _deployment(args.config)
  async with Runtime(servers, name="micro.cli") as runtime:
    declarations = Declarations(runtime, "commands")
    if args.action == "list":
      view = await declarations.view()
      print(
        json.dumps(
          {
            key: {
              "state": declared.state.value,
              "applied": declared.hash,
              "live_versions": sorted(declared.live_hashes),
            }
            for key, declared in view.items()
          },
          indent=2,
        )
      )
      return 0
    if args.action == "forget" and not await declarations.forget(args.command):
      print(f"No applied command {args.command!r}.")
      return 1
    http = DiscordHTTPClient(runtime)
    application = await http.call("get_my_application")
    locks = await runtime.locks()
    async with locks.hold(SYNC_LOCK, ttl=30):
      changed = await sync_commands(runtime, http, str(application["id"]))
    print(
      "Synced changed command scopes." if changed else "Commands were already in sync."
    )
  return 0
