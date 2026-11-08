"""The `micro` command line."""

import argparse
import asyncio
import json
import logging
import math
import os
import re
import sys
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from nats.errors import NoServersError

from micro import subjects
from micro.runtime import Runtime, event_loop_factory

DEFAULT_CONFIG = "micro.toml"


def main(argv: Sequence[str] | None = None) -> int:
  parser = _parser()
  args = parser.parse_args(argv)
  if getattr(args, "handler", None) is None:
    parser.print_help()
    return 0
  if args.handler is not _help_handler and args.command not in {"docs", "init"}:
    from micro import _dotenv

    _dotenv.load()
  level = "DEBUG" if args.verbose else os.environ.get("MICRO_LOG_LEVEL", "INFO").upper()
  from micro import _logging

  _logging.configure(level)
  sys.path.insert(0, os.getcwd())
  try:
    with asyncio.Runner(loop_factory=event_loop_factory) as runner:
      return runner.run(args.handler(args)) or 0
  except KeyboardInterrupt:
    return 130
  except (ConnectionError, FileExistsError, FileNotFoundError, ValueError) as error:
    print(f"micro: {error}", file=sys.stderr)
    return 1


def _version() -> str:
  from importlib.metadata import PackageNotFoundError, version

  try:
    return version("discord-micro")
  except PackageNotFoundError:
    return "unknown"


GROUPS: dict[str, tuple[str, ...]] = {
  "Project": ("init", "services", "pkg", "docs", "invite", "help"),
  "Run": ("dev", "server", "worker", "nodes", "configure"),
  "Discord": ("commands",),
}
"""How `micro --help` sections the commands."""


class _Commands(argparse._SubParsersAction):  # pyright: ignore[reportPrivateUsage]
  """Subcommand registry: a command's description defaults to its one-line help."""

  def add_parser(self, name: str, **kwargs: Any) -> argparse.ArgumentParser:
    help_text = kwargs.get("help")
    if help_text and not kwargs.get("description"):
      kwargs["description"] = help_text[0].upper() + help_text[1:]
    return super().add_parser(name, **kwargs)


class _Parser(argparse.ArgumentParser):
  """Every parser in the CLI.

  One with subcommands lists them the same way wherever it sits: the top level, a
  group (`micro pkg`), a group's group (`micro pkg source`). Run bare it shows that
  help, and it ends with a `help` subcommand. A parser without subcommands is a leaf
  and has only `-h/--help`.
  """

  def __init__(self, *args: Any, **kwargs: Any) -> None:
    super().__init__(*args, **kwargs)
    self.register("action", "parsers", _Commands)

  def add_subparsers(self, **kwargs: Any) -> Any:
    kwargs.setdefault("metavar", "command")
    actions = super().add_subparsers(**kwargs)
    if "handler" not in self._defaults:  # a command that also runs keeps its handler
      self.set_defaults(handler=_help_handler, target=self, topic=[])
    return actions

  def commands(self) -> argparse._SubParsersAction | None:  # pyright: ignore[reportPrivateUsage, reportMissingTypeArgument]
    return next(
      (a for a in self._actions if isinstance(a, argparse._SubParsersAction)),  # pyright: ignore[reportPrivateUsage]
      None,
    )

  def command_help(self) -> dict[str, str]:
    actions = self.commands()
    if actions is None:
      return {}
    return {str(a.metavar): a.help or "" for a in actions._choices_actions}  # pyright: ignore[reportPrivateUsage]

  def sections(self) -> dict[str, tuple[str, ...]]:
    """The command listing's sections (title to names)."""
    return {"commands": tuple(self.command_help())}

  def format_help(self) -> str:
    if self.commands() is None:
      return super().format_help()
    formatter = self._get_formatter()
    formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
    formatter.add_text(self.description)
    described = self.command_help()
    for title, names in self.sections().items():
      formatter.start_section(title)
      for name in names:
        formatter.add_argument(
          argparse.Action([], dest=name, metavar=name, help=described[name])
        )
      formatter.end_section()
    options = [a for a in self._actions if a.option_strings]
    if options:
      formatter.start_section("options")
      formatter.add_arguments(options)
      formatter.end_section()
    formatter.add_text(
      f"Run `{self.prog} help COMMAND` or `{self.prog} COMMAND -h` for a command's own help."
    )
    return formatter.format_help() + self.footer()

  def footer(self) -> str:
    return ""


class _Root(_Parser):
  """The top level: commands by purpose, then the common tasks."""

  def sections(self) -> dict[str, tuple[str, ...]]:
    return GROUPS

  def footer(self) -> str:
    return (
      "\ncommon tasks:\n"
      "  micro init                    start a project in this directory\n"
      "  micro services add tickets    add a service\n"
      "  micro dev                     run everything on this machine\n"
      "  micro nodes list              see what is running\n"
    )


async def _help_handler(args: argparse.Namespace) -> int:
  """`micro help`, `micro pkg help source`, and a group run without a command."""
  target: _Parser = args.target
  for name in args.topic:
    actions = target.commands()
    if actions is None or name not in actions.choices:
      raise ValueError(
        f"No command {name!r} under `{target.prog}`; see `{target.prog} help`."
      )
    target = actions.choices[name]
  target.print_help()
  return 0


def _add_help_commands(parser: _Parser) -> None:
  """End every parser that has subcommands with a `help` subcommand."""
  actions = parser.commands()
  if actions is None:
    return
  for child in list(actions.choices.values()):
    _add_help_commands(child)
  if "help" not in actions.choices:
    leaf = actions.add_parser("help", help="show this help, or a command's")
    leaf.add_argument(
      "topic", nargs="*", metavar="command", help="a command, as in `help source add`"
    )
    leaf.set_defaults(handler=_help_handler, target=parser)


def _parser() -> argparse.ArgumentParser:
  parser = _Root(prog="micro", description=__doc__)
  parser.add_argument(
    "-v", "--version", action="version", version=f"micro {_version()}"
  )
  parser.add_argument(
    "-V", "--verbose", action="store_true", help="debug logging (any command)"
  )
  commands = parser.add_subparsers(dest="command", parser_class=_Parser)

  def command(name: str, help: str, description: str | None = None) -> _Parser:
    return commands.add_parser(name, help=help, description=description)

  config = argparse.ArgumentParser(add_help=False)
  config.add_argument("--config", default=DEFAULT_CONFIG, help="micro.toml to read")

  docs = command("docs", "open the documentation in a browser")
  docs.add_argument("--no-browser", action="store_true", help="only print the address")
  docs.set_defaults(handler=_docs)

  invite = command("invite", "print the links that add the bot to a server or account")
  invite.add_argument(
    "-p",
    "--permissions",
    help="comma-separated names or a number (default: [invite] in micro.toml)",
  )
  invite.add_argument("--guild", metavar="ID", help="preselect this server")
  invite.add_argument(
    "--application-id", help="use this instead of reading it from DISCORD_TOKEN"
  )
  invite.add_argument("--config", default=DEFAULT_CONFIG, help="micro.toml to read")
  invite.set_defaults(handler=_invite)

  init = command("init", "add Micro to the project in this directory")
  init.set_defaults(handler=_init)

  services = command("services", "the services in this project")
  services_actions = services.add_subparsers()
  service_add = services_actions.add_parser("add", help="a new, empty service")
  service_add.add_argument("name")
  service_add.set_defaults(handler=_services, action="add")
  services_actions.add_parser(
    "list", help="the services here, and which came from a package"
  ).set_defaults(handler=_services, action="list")

  pkg = command(
    "pkg", "packages: examples to copy in from a git source, edit, and upgrade"
  )
  pkg_actions = pkg.add_subparsers()
  pkg_list = pkg_actions.add_parser(
    "list",
    help="the packages in each source, and which you have added",
    parents=[config],
  )
  pkg_list.add_argument("source", nargs="?", help="only this source")
  pkg_list.set_defaults(handler=_pkg, action="list")
  pkg_add = pkg_actions.add_parser(
    "add",
    help="copy a package into services/ (a template needs a name)",
    parents=[config],
  )
  pkg_add.add_argument("package", help="SOURCE/NAME, as in builtin/chat")
  pkg_add.add_argument(
    "name",
    nargs="?",
    help="what to call the copy of a template, as in `builtin/tpl tickets`",
  )
  pkg_add.add_argument("--ref", help="a branch, tag or commit (default: the source's)")
  pkg_add.set_defaults(handler=_pkg, action="add")
  pkg_status = pkg_actions.add_parser(
    "status", help="your packages against what their sources ship", parents=[config]
  )
  pkg_status.add_argument("names", nargs="*", metavar="name")
  pkg_status.set_defaults(handler=_pkg, action="status")
  pkg_diff = pkg_actions.add_parser(
    "diff",
    help="a package's files, yours against what its source ships",
    parents=[config],
  )
  pkg_diff.add_argument("name")
  pkg_diff.set_defaults(handler=_pkg, action="diff")
  pkg_upgrade = pkg_actions.add_parser(
    "upgrade",
    help="bring packages up to what their sources ship, merging your edits",
    parents=[config],
  )
  pkg_upgrade.add_argument("names", nargs="*", metavar="name")
  pkg_upgrade.add_argument(
    "--ref", help="move one package to this branch, tag or commit"
  )
  settle = pkg_upgrade.add_mutually_exclusive_group()
  settle.add_argument(
    "--theirs", action="store_true", help="on a conflict, take the source's file"
  )
  settle.add_argument(
    "--mine",
    action="store_true",
    help="on a conflict, keep yours and mark the source's as reviewed",
  )
  pkg_upgrade.set_defaults(handler=_pkg, action="upgrade")
  pkg_forget = pkg_actions.add_parser(
    "forget", help="stop tracking a package; its files stay", parents=[config]
  )
  pkg_forget.add_argument("name")
  pkg_forget.set_defaults(handler=_pkg, action="forget")
  pkg_source = pkg_actions.add_parser("source", help="where packages come from")
  source_actions = pkg_source.add_subparsers()
  source_add = source_actions.add_parser(
    "add",
    help="add or replace a source in micro.toml",
    description="Add or replace a source in micro.toml. A git URL may be https or ssh: "
    "the other form of the same address is tried if the first fails.",
    parents=[config],
  )
  source_add.add_argument("name", help="what to call it, as in NAME/package")
  source_add.add_argument("location", help="a git URL, or a folder on this machine")
  source_add.add_argument(
    "path",
    nargs="?",
    help="the folder of packages inside the repository (default: packages)",
  )
  source_add.add_argument("--ref", help="a branch, tag or commit to follow")
  source_add.set_defaults(handler=_pkg, action="source_add")
  source_actions.add_parser(
    "list", help="the sources, with where they point", parents=[config]
  ).set_defaults(handler=_pkg, action="source_list")
  source_remove = source_actions.add_parser(
    "remove", help="remove a source from micro.toml", parents=[config]
  )
  source_remove.add_argument("name")
  source_remove.set_defaults(handler=_pkg, action="source_remove")

  server = command("server", "the NATS server everything connects to, on its own")
  server_actions = server.add_subparsers()
  server_start = server_actions.add_parser(
    "start", help="run it in the foreground (data in [nats_server] store_dir)"
  )
  server_start.add_argument("config", nargs="?", default=DEFAULT_CONFIG)
  server_start.set_defaults(handler=_server, action="start")
  server_actions.add_parser(
    "status",
    help="is it reachable, is JetStream on, which nodes are connected",
    parents=[config],
  ).set_defaults(handler=_server, action="status")

  dev = command(
    "dev",
    "run the whole bot on this machine",
    "Starts the NATS server if none is running, then runs every process group in "
    "micro.toml and keeps them running; Ctrl-C stops them in order. `scale` and "
    "`roll` change a running one.",
  )
  dev.add_argument("-c", "--config", default=DEFAULT_CONFIG, help="micro.toml to run")
  dev.add_argument(
    "--name", help="this machine's name among the nodes (default: hostname)"
  )
  dev.set_defaults(handler=_dev, action=None)
  dev_actions = dev.add_subparsers(metavar="[command]")
  dev_scale = dev_actions.add_parser(
    "scale", help="change the replicas of a process group", parents=[config]
  )
  dev_scale.add_argument("process")
  dev_scale.add_argument("replicas", type=int)
  dev_scale.set_defaults(handler=_dev, action="scale")
  dev_roll = dev_actions.add_parser(
    "roll",
    help="replace every replica of a process group, one at a time",
    parents=[config],
  )
  dev_roll.add_argument("process")
  dev_roll.set_defaults(handler=_dev, action="roll")
  for leaf in (dev_scale, dev_roll):
    leaf.add_argument("--node", help="which node (default: the one running the group)")

  nodes = command("nodes", "the machines running your bot")
  nodes_actions = nodes.add_subparsers()
  nodes_list = nodes_actions.add_parser(
    "list", help="each node, its processes, and the live components", parents=[config]
  )
  nodes_list.add_argument("--json", action="store_true", help="machine-readable output")
  nodes_list.set_defaults(handler=_nodes, action="list")

  worker = command(
    "worker",
    "one process hosting components, connected to the server",
    "Connects to the NATS server and hosts components in this one process until "
    "Ctrl-C. It is the server's pair: `micro dev` starts one worker per process "
    "group replica in micro.toml and keeps them running. Name what to host as a "
    "process group from micro.toml (`app`), or a component: module:attribute, or "
    "package.* for every component in a package. micro.toml also supplies the NATS "
    "address.",
  )
  worker.add_argument(
    "targets",
    nargs="*",
    metavar="target",
    help="a process group (app), or module:attribute / package.* to host",
  )
  worker.add_argument("--config", default=DEFAULT_CONFIG, help="micro.toml to read")
  worker.add_argument(
    "--nats", help="NATS URL(s), comma separated (default: micro.toml)"
  )
  worker.add_argument("--name", help="name shown in presence")
  worker.set_defaults(handler=_worker)

  slash = command("commands", "inspect and sync Discord application commands")
  slash_actions = slash.add_subparsers()
  slash_list = slash_actions.add_parser(
    "list", help="commands, their state, and live versions", parents=[config]
  )
  slash_list.add_argument("--json", action="store_true", help="machine-readable output")
  slash_list.set_defaults(handler=_commands, action="list")
  slash_actions.add_parser(
    "sync", help="sync now, repairing commands changed outside Micro", parents=[config]
  ).set_defaults(handler=_commands, action="sync")
  forget = slash_actions.add_parser(
    "forget", help="drop a retired service's commands, then sync", parents=[config]
  )
  forget.add_argument("service")
  forget.set_defaults(handler=_commands, action="forget")

  configure = command(
    "configure",
    "view and edit the shared configuration",
    description=(
      "A full-screen editor for the shared configuration tables every process follows "
      "(the Gateway's settings, and any table you add under [config] in micro.toml). "
      "Optionally open a table directly."
    ),
  )
  configure.add_argument("name", nargs="?", help="a table to open, e.g. gateway")
  configure.add_argument("--config", default=DEFAULT_CONFIG, help="micro.toml to read")
  configure.set_defaults(handler=_configure)

  _add_help_commands(parser)
  return parser


async def _docs(args: argparse.Namespace) -> int:
  from micro._docs import serve

  await serve(browser=not args.no_browser)
  return 0


def _configured_permissions(path: str) -> list[str | int]:
  """The `[invite] permissions` of micro.toml, or none without a file."""
  import tomllib

  try:
    with open(path, "rb") as file:
      return list(tomllib.load(file).get("invite", {}).get("permissions", []))
  except FileNotFoundError:
    return []


async def _invite(args: argparse.Namespace) -> int:

  from micro.discord.invite import (
    application_id,
    invite_url,
    parse_permissions,
  )

  token = os.environ.get("DISCORD_TOKEN")
  application = (
    args.application_id
    or os.environ.get("DISCORD_APPLICATION_ID")
    or (application_id(token) if token else None)
  )
  if application is None:
    raise ValueError(
      "Set DISCORD_TOKEN (in .env or the environment) or pass --application-id."
    )
  if args.permissions is not None:
    names: list[str | int] = args.permissions.split(",")
  else:
    names = _configured_permissions(args.config)
  permissions = parse_permissions(names)
  print("Add to a server (bot and slash commands):")
  print(f"  {invite_url(application, permissions=permissions, guild_id=args.guild)}")
  print("Install on a user account (slash commands only):")
  print(f"  {invite_url(application, install='user')}")
  if permissions:
    from micro.discord.invite import Permissions

    listed = ", ".join(
      name.lower()
      for name, flag in Permissions.__members__.items()
      if flag in permissions
    )
    print(f"Permissions: {listed} (= {int(permissions)})")
  else:
    print(
      "No permissions requested; set [invite] permissions in micro.toml or pass -p."
    )
  return 0


async def _init(args: argparse.Namespace) -> int:
  from micro.scaffold import init

  project = init()
  services = project.services.relative_to(project.root)
  hello = (project.services / "hello").is_dir()
  added = f"micro.toml and {services}/hello/" if hello else "micro.toml"
  print(f"Added {added}.\n\n  DISCORD_TOKEN=... micro dev")
  return 0


_WORDS: dict[str, str] = {
  "upgrade": "upgrade",
  "add": "new file",
  "remove": "removed upstream",
  "refresh": "already matches",
  "orphan": "no longer shipped (yours kept)",
  "dropped": "no longer shipped",
  "modified": "edited by you",
  "deleted": "deleted by you",
  "conflict": "CONFLICT: changed by you and upstream",
  "gone": "CONFLICT: deleted by you, changed upstream",
  "markers": "CONFLICT: fix the <<<<<<< markers",
  "merged": "merged with your edits",
  "theirs": "replaced with upstream's",
  "mine": "kept yours; upstream's marked reviewed",
}


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
  """A Markdown table, padded so it reads as columns in a terminal too."""
  cells = [[cell.replace("|", "\\|") for cell in row] for row in (headers, *rows)]
  widths = [max(len(cell) for cell in column) for column in zip(*cells)]

  def line(row: Sequence[str]) -> str:
    return (
      "| " + " | ".join(cell.ljust(width) for cell, width in zip(row, widths)) + " |"
    )

  rule = "| " + " | ".join("-" * width for width in widths) + " |"
  return "\n".join([line(cells[0]), rule, *map(line, cells[1:])])


def _is_git(location: str) -> bool:
  return (
    "://" in location
    or location.endswith(".git")
    or bool(re.fullmatch(r"[\w.-]+@[\w.-]+:.+", location))
  )


async def _pkg_source(args: argparse.Namespace) -> int:
  from micro.scaffold import _sources, find

  project = find()
  if args.action == "source_list":
    sources = _sources.configured(project.root)
    rows = [
      [s.name, s.where, s.path if s.url else "", s.ref or "default"]
      for s in sources.values()
    ]
    print(_table(["SOURCE", "WHERE", "PATH", "REF"], rows))
    return 0
  if args.action == "source_remove":
    _sources.remove(project.root, args.name)
    print(f"Removed source {args.name!r}; packages already added keep their files.")
    return 0
  _sources.check_name(args.name)
  if _is_git(args.location):
    path = (args.path or _sources.DEFAULT_PATH).strip("/")
    source = _sources.Source(args.name, args.location, path, args.ref)
  else:
    source = _sources.Source(args.name, None, args.location)
  _sources.save(project.root, source)
  print(f"Saved source {args.name!r} in micro.toml.")
  try:
    resolved = _sources.resolve(source)
    tree = _sources.tree(source, resolved.commit, project.root)
  except (OSError, ValueError, RuntimeError) as error:
    print(f"Could not read it yet: {error}", file=sys.stderr)
    return 1
  shipped = _sources.packages_in(tree)
  at = f" at {resolved.ref}@{resolved.commit[:7]}" if resolved.commit else ""
  print(
    f"It has {len(shipped)} package(s){at}: {', '.join(sorted(shipped)) or 'none'}."
  )
  return 0


async def _pkg(args: argparse.Namespace) -> int:
  from micro.scaffold import find, packages

  if args.action.startswith("source_"):
    return await _pkg_source(args)
  if args.action == "list":
    try:
      project = find()
    except FileNotFoundError:
      project = None
    root = project.root if project else Path.cwd()
    entries = packages.Lock.load(project).entries.values() if project else ()
    for found in packages.listing(root, args.source):
      source = found.source
      at = ""
      if found.resolved and found.resolved.commit:
        at = f"  {found.resolved.ref}@{found.resolved.commit[:7]}"
      print(f"{source.name}  {source.where}{at}")
      if found.problem:
        print(f"  can't read it: {found.problem}")
      rows = [
        [
          package,
          summary,
          ", ".join(
            sorted(
              e.path
              for e in entries
              if e.package == package and e.source == source.name
            )
          ),
        ]
        for package, summary in found.packages.items()
      ]
      if rows:
        print(_table(["PACKAGE", "WHAT IT IS", "ADDED AS"], rows))
      print()
    return 0
  project = find()
  if args.action == "add":
    folder = packages.add(args.package, project, name=args.name, ref=args.ref)
    print(
      f"Added {folder.relative_to(project.root)}/; `micro dev` loads it with the other services."
    )
    return 0
  if args.action == "forget":
    packages.forget(project, args.name)
    print(f"{args.name} is no longer tracked; its files are unchanged.")
    return 0
  if args.action == "diff":
    text = packages.diff(project, args.name)
    print(
      text or f"{args.name} matches what its source ships.", end="" if text else "\n"
    )
    return 0
  names = args.names or None
  if args.action == "status":
    reports = packages.status(project, names)
  else:
    settle = "theirs" if args.theirs else "mine" if args.mine else None
    reports = packages.upgrade(project, names, settle=settle, ref=args.ref)
  if not reports:
    print("No packages added yet. See `micro pkg list`.")
  open_items = 0
  rows: list[list[str]] = []
  for report in reports:
    notable = [c for c in report.changes if c.kind != "current"]
    origin = f"{report.source}@{report.ref}" if report.ref else report.source
    if report.commit:
      origin += f" ({report.commit[:7]})"
    if not report.shipped:
      reason = (
        report.problem or f"the {report.source} source no longer has {report.package}"
      )
      rows.append([report.path, origin, f"can't compare: {reason}", ""])
      continue
    headline = "up to date" if not notable else ""
    if report.attention:
      headline = "needs a decision"
    elif any(c.kind in packages.PENDING for c in notable):
      headline = "upgrade available" if args.action == "status" else "upgraded"
    elif any(c.kind == "merged" for c in notable):
      headline = "merged"
    elif notable:
      headline = "up to date, with your edits"
    rows.append([report.path, origin, headline, ""])
    for change in notable:
      rows.append(["", "", f"  {change.file}", _WORDS.get(change.kind, change.kind)])
    open_items += len(report.attention)
  if rows:
    print(_table(["PACKAGE", "SOURCE", "STATUS", "CHANGE"], rows))
  if open_items:
    print(
      "\nResolve the <<<<<<< markers in the files above, or run "
      "`micro pkg upgrade --theirs` (take upstream's) or `--mine` (keep yours); "
      "`micro pkg diff NAME` shows the difference."
    )
  return 1 if open_items else 0


def _is_group(target: str) -> bool:
  """A process group name, not a component target (`module:attribute`, `package.*`)."""
  return ":" not in target and not target.endswith(".*")


async def _worker(args: argparse.Namespace) -> int:
  from micro.launch import load_components, load_config

  groups = [t for t in args.targets if _is_group(t)]
  targets = [t for t in args.targets if not _is_group(t)]
  path = Path(args.config)
  config = None
  if path.is_file():
    config = load_config(path)
  elif groups:
    raise FileNotFoundError(f"No {path}: run `micro init`, or pass --config.")
  servers = args.nats.split(",") if args.nats else None
  name = args.name
  replicas = 1
  if config is not None:
    for group in groups:
      if group not in config.processes:
        known = ", ".join(sorted(config.processes))
        raise ValueError(f"No process group {group!r} in {path}; it has: {known}.")
      targets.extend(config.processes[group].components)
    servers = servers or (
      os.environ["MICRO_NATS_URL"].split(",")
      if "MICRO_NATS_URL" in os.environ
      else config.nats
    )
    name = name or ".".join([config.name, *(["+".join(groups)] if groups else [])])
    replicas = config.jetstream_replicas
  if not targets:
    raise ValueError(
      "Nothing to host: name a process group from micro.toml (such as `app`) "
      "or a component (module:attribute, package.*)."
    )
  components = load_components(targets)
  runtime = Runtime(servers, name=name or "micro", replicas=replicas)
  await runtime.serve(*components)
  return 0


async def _dev(args: argparse.Namespace) -> int:
  if args.action is None:
    return await _dev_start(args)
  return await _operate(args)


async def _dev_start(args: argparse.Namespace) -> int:
  from micro.launch import NatsServer, Node, load_config

  path = Path(args.config)
  config = load_config(path)
  server = NatsServer(config, path)
  started = False
  if config.local_nats() is not None and config.nats_server.enabled:
    if await server.reachable():
      logging.getLogger("micro").info(
        "Using the NATS server already running at %s:%d", *server.address
      )
    else:
      await server.start()
      started = True
  try:
    await Node(config, path, name=args.name).run()
  finally:
    if started:
      await server.stop()
  return 0


async def _server(args: argparse.Namespace) -> int:
  from micro.launch import NODE_KIND, DeploymentConfig, NatsServer, load_config

  path = Path(args.config)
  config = load_config(path) if path.exists() else DeploymentConfig()
  if args.action == "start":
    server = NatsServer(config, path)
    if await server.reachable():
      host, port = server.address
      raise ValueError(f"A NATS server is already running at {host}:{port}.")
    return await server.run()
  async with _connect(config.nats) as runtime:
    info = await runtime.jetstream.account_info()
    print(
      json.dumps(
        {
          "server": runtime.nats.connected_url.netloc
          if runtime.nats.connected_url
          else None,
          "jetstream": {"streams": info.streams, "consumers": info.consumers},
          "nodes": sorted(
            f"{entry.metadata.get('deployment')}/{entry.name}"
            for entry in runtime.directory.entries(NODE_KIND)
          ),
        },
        indent=2,
      )
    )
  return 0


def _nodes_of(runtime: Runtime, name: str) -> dict[str, Any]:
  from micro.launch import NODE_KIND

  nodes = {
    entry.name: entry
    for entry in runtime.directory.entries(NODE_KIND)
    if entry.metadata.get("deployment") == name
  }
  if not nodes:
    raise ConnectionError(
      f"No node is running for {name!r}. Start one with `micro dev`."
    )
  return nodes


async def _nodes(args: argparse.Namespace) -> int:
  from micro.launch import NODE_KIND

  name, servers = _deployment(args.config)
  async with _connect(servers) as runtime:
    nodes = _nodes_of(runtime, name)
    report: dict[str, Any] = {"ok": True, "nodes": {}, "components": []}
    for node in sorted(nodes):
      reply = await runtime.nats.request(
        subjects.node(name, node, "ps"), b"{}", timeout=30
      )
      answer = json.loads(reply.data)
      report["nodes"][node] = {key: v for key, v in answer.items() if key != "ok"}
    for entry in runtime.directory.entries():
      if entry.kind not in ("runtime", NODE_KIND):
        report["components"].append(
          {"kind": entry.kind, "name": entry.name, "runtime": entry.instance[:8]}
        )
    if args.json:
      print(json.dumps(report, indent=2))
      return 0
    processes = [
      [node, p["group"], str(p["pid"]), _age(p["uptime"])]
      for node, body in report["nodes"].items()
      for p in body["processes"]
    ]
    print(_table(["NODE", "GROUP", "PID", "UP"], processes))
    components = [[c["kind"], c["name"], c["runtime"]] for c in report["components"]]
    if components:
      print()
      print(_table(["KIND", "COMPONENT", "RUNTIME"], components))
  return 0


def _age(seconds: int) -> str:
  hours, rest = divmod(int(seconds), 3600)
  minutes, seconds = divmod(rest, 60)
  if hours:
    return f"{hours}h {minutes}m"
  return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"


async def _operate(args: argparse.Namespace) -> int:
  name, servers = _deployment(args.config)
  async with _connect(servers) as runtime:
    target = _target(args, _nodes_of(runtime, name))
    request: dict[str, Any] = {"process": args.process}
    if args.action == "scale":
      request["replicas"] = args.replicas
    reply = await runtime.nats.request(
      subjects.node(name, target, args.action),
      json.dumps(request).encode(),
      # Rolling waits for each replacement to become ready, however long that is.
      timeout=math.inf if args.action == "roll" else 30,
    )
    body = json.loads(reply.data)
    print(json.dumps(body, indent=2))
    return 0 if body.get("ok") else 1


async def _services(args: argparse.Namespace) -> int:
  from micro.scaffold import add_service, find, packages

  project = find()
  if args.action == "add":
    folder = add_service(project, args.name)
    print(
      f"Added {folder.relative_to(project.root)}/; `micro dev` loads it with the other services."
    )
    return 0
  copies = {
    Path(entry.path).name: entry
    for entry in packages.Lock.load(project).entries.values()
  }
  rows: list[list[str]] = []
  for item in sorted(project.services.iterdir()):
    if item.name.startswith(("_", ".")):
      continue
    if item.is_dir() and (item / "__init__.py").is_file():
      key = item.name
    elif item.suffix == ".py":
      key = item.stem
    else:
      continue
    entry = copies.get(key)
    blank = entry is None or entry.package == "service"
    origin = (
      "yours" if blank or entry is None else f"from {entry.package} ({entry.source})"
    )
    rows.append([key, origin])
  if rows:
    print(_table(["SERVICE", "ORIGIN"], rows))
  return 0


def _target(args: argparse.Namespace, nodes: dict[str, Any]) -> str:
  """The node a scale or roll goes to: --node, or the one running that group."""
  if args.node:
    if args.node not in nodes:
      raise ValueError(f"No node {args.node!r}; running: {', '.join(sorted(nodes))}.")
    return args.node
  running = sorted(
    node
    for node, entry in nodes.items()
    if args.process in (entry.metadata.get("processes") or [])
  )
  if not running:
    raise ValueError(f"No node runs a process group {args.process!r}.")
  if len(running) > 1:
    raise ValueError(
      f"Several nodes run {args.process!r} ({', '.join(running)}); pass --node."
    )
  return running[0]


@asynccontextmanager
async def _connect(servers: list[str] | None) -> AsyncIterator[Runtime]:
  """A CLI runtime, with a plain message when no NATS server answers."""

  # nats-py keeps retrying a refused first connection for minutes (each try printing a
  # traceback) unless it is told to give up after two quick attempts.
  async def quiet(error: Exception) -> None:
    del error

  runtime = Runtime(
    servers,
    name="micro.cli",
    max_reconnect_attempts=1,
    reconnect_time_wait=0,
    error_cb=quiet,
  )
  try:
    await runtime.start()
  except (NoServersError, OSError, TimeoutError) as error:
    raise ConnectionError(
      f"No NATS server at {', '.join(runtime.servers)}. Start one with "
      "`micro server start`, or run `micro dev`."
    ) from error
  try:
    yield runtime
  finally:
    await runtime.close()


def _deployment(path: str) -> tuple[str, list[str] | None]:
  from micro.launch import load_config

  if Path(path).exists():
    config = load_config(path)
    return config.name, config.nats
  return "micro", None


async def _configure(args: argparse.Namespace) -> int:
  from micro._configure import BUILTIN_MODELS, Configure, load_model, run
  from micro._tui import Terminal

  name, servers = _deployment(args.config)
  targets = dict(BUILTIN_MODELS)
  if Path(args.config).exists():
    from micro.launch import load_config

    targets.update(load_config(args.config).config)
  models: dict[str, Any] = {key: load_model(target) for key, target in targets.items()}
  async with _connect(servers) as runtime:
    table = await runtime.table(subjects.CONFIG_BUCKET, dict)
    app = Configure(
      table,
      models,
      title=f"{name}  ·  {','.join(servers or [])}".rstrip(" ·,"),
    )
    if not Terminal.interactive():
      await app.load()
      for doc_name in app.names:
        doc = app.docs[doc_name]
        if args.name not in (None, doc_name):
          continue
        print(
          f"{doc_name}  (revision {doc.revision})"
          if doc.value is not None
          else f"{doc_name}  (not created)"
        )
        for key, value in (doc.value or {}).items():
          print(f"  {key}  {json.dumps(value)}")
      print("(run it in a terminal to edit)", file=sys.stderr)
      return 0
    await app.load()
    if args.name in app.names:
      app.table_cursor = app.names.index(args.name)
      if app.doc is not None and app.doc.value is not None:
        app.focus = "fields"
    elif args.name:
      print(f"No configuration named {args.name!r}.", file=sys.stderr)
      return 1
    with Terminal() as terminal:

      def external(text: str) -> str:
        import shlex
        import subprocess
        import tempfile

        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as file:
          file.write(text)
          path = file.name
        try:
          with terminal.suspended():
            status = subprocess.call([*shlex.split(editor), path])
          if status:
            raise ValueError(f"{editor} exited with status {status}")
          return Path(path).read_text()
        finally:
          os.unlink(path)

      app.external_editor = external
      await run(app, terminal)
  return 0


async def _commands(args: argparse.Namespace) -> int:
  from micro.coordination import Declarations
  from micro.discord import DiscordHTTPClient
  from micro.discord.interactions import SYNC_LOCK, SyncFailed, sync_commands

  _, servers = _deployment(args.config)
  async with _connect(servers) as runtime:
    declarations = Declarations(runtime, "commands")
    if args.action == "list":
      view = await declarations.view()
      if args.json:
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
      rows = [
        [
          key,
          declared.state.value,
          str(declared.hash),
          ", ".join(sorted(declared.live_hashes)),
        ]
        for key, declared in view.items()
      ]
      print(
        _table(["COMMAND", "STATE", "APPLIED", "LIVE VERSIONS"], rows)
        if rows
        else "No commands declared."
      )
      return 0
    if args.action == "forget" and not await declarations.forget(args.command):
      print(f"No applied command {args.command!r}.")
      return 1
    http = DiscordHTTPClient(runtime)
    application = await http.call("get_my_application")
    locks = await runtime.locks()
    async with locks.hold(SYNC_LOCK, ttl=30):
      try:
        changed = await sync_commands(
          runtime, http, str(application["id"]), verify=True
        )
      except SyncFailed as failure:
        for scope, error in sorted(failure.failures.items()):
          print(f"{scope}: {error}", file=sys.stderr)
        return 1
    print(
      "Synced changed command scopes." if changed else "Commands were already in sync."
    )
  return 0
