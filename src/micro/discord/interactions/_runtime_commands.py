"""Commands created while the bot runs (custom commands, per-guild commands)."""

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from nats.errors import Error as NatsError
from nats.js.errors import NotFoundError
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from micro import log, subjects
from micro.coordination import Table
from micro.discord.enums import CommandType, InteractionType
from micro.discord.routes import command_route
from micro.runtime import StreamConsumer, default_backoff

from ._commands import Handler, _validate_name
from ._context import Interaction
from ._inject import call
from ._templates import (
  INTERACTIONS_KEY,
  Call,
  InteractionTemplate,
  ensure_interactions_stream,
  route_consumer,
)

if TYPE_CHECKING:
  from micro.service import Service

PREFIX = "rtcmd."
"""Table keys of runtime commands: `rtcmd.<type>.<name>`."""


class _Stored(BaseModel):
  model_config = ConfigDict(extra="ignore")

  definition: dict[str, JsonValue]
  guilds: list[str] = Field(default_factory=list)
  everywhere: bool = False


def option(
  name: str,
  description: str = "-",
  *,
  kind: str = "string",
  required: bool = False,
  choices: Sequence[str | int | float] | None = None,
) -> dict[str, JsonValue]:
  """A command option for `RuntimeCommands.add`: `option("word", kind="string")`.

  `kind` is one of string, integer, boolean, user, channel, role, mentionable,
  number, attachment.
  """
  kinds = {
    "string": 3,
    "integer": 4,
    "boolean": 5,
    "user": 6,
    "channel": 7,
    "role": 8,
    "mentionable": 9,
    "number": 10,
    "attachment": 11,
  }
  if kind not in kinds:
    raise ValueError(f"Unknown option kind {kind!r}.")
  value: dict[str, JsonValue] = {
    "type": kinds[kind],
    "name": _validate_name(name),
    "description": description,
    "required": required,
  }
  if choices:
    value["choices"] = [{"name": str(item), "value": item} for item in choices]
  return value


def table_key(kind: int, name: str) -> str:
  return f"{PREFIX}{kind}.{name}"


async def runtime_table(runtime: Any) -> Table[_Stored]:
  return await runtime.table(subjects.STATE_BUCKET, _Stored)


async def runtime_definitions(runtime: Any) -> dict[str, dict[str, JsonValue]]:
  """Runtime commands as sync definitions, keyed `type:name` like declared ones."""
  table = await runtime_table(runtime)
  definitions: dict[str, dict[str, JsonValue]] = {}
  for key, entry in (await table.items(PREFIX + ">")).items():
    kind, _, name = key.removeprefix(PREFIX).partition(".")
    stored = entry.value
    guilds: list[JsonValue] = [*stored.guilds]
    if stored.everywhere:
      definitions[f"{kind}:{name}"] = {**stored.definition, "guild_ids": []}
    if guilds:
      suffix = "" if not stored.everywhere else "#guilds"
      definitions[f"{kind}:{name}{suffix}"] = {
        **stored.definition,
        "guild_ids": guilds,
      }
  return definitions


class RuntimeCommands(InteractionTemplate):
  """Commands that are created, changed, and removed while the bot runs.

      dynamic = RuntimeCommands(service)

      @dynamic.handler
      async def run(ctx: Interaction) -> None:
        await ctx.respond(await lookup(ctx.guild_id, ctx.command_name))

      await dynamic.add("hello", "Say hello", guild_id=1234)
      await dynamic.remove("hello", guild_id=1234)

  Commands are stored (they survive restarts and are shared by every replica
  and service using the same names), registered with Discord by `CommandSync`
  within moments, and every one runs the single `handler`. A command that exists
  in several guilds is one name: tell them apart with `ctx.guild_id`. Names
  must differ from commands declared in code (the declared one wins).
  """

  def __init__(self, service: Service) -> None:
    super().__init__(service)
    self._handler: Handler | None = None
    self._autocomplete: Handler | None = None
    self._names: set[tuple[int, str]] = set()
    self._running: dict[str, StreamConsumer] = {}
    self._table: Table[_Stored] | None = None
    self._watching: asyncio.Task[None] | None = None

  def handler(self, function: Handler) -> Handler:
    """The function that runs any runtime command: `async def f(ctx)`."""
    if not asyncio.iscoroutinefunction(function):
      raise TypeError("Interaction handlers must be async functions.")
    self._handler = function
    return function

  def autocomplete(self, function: Handler) -> Handler:
    """Suggestions for options declared `autocomplete=True`: `async def f(ctx, value)`."""
    self._autocomplete = function
    return function

  # Managing commands (any service may call these) ------------------------------

  async def add(
    self,
    name: str,
    description: str = "-",
    *,
    guild_id: int | str | None = None,
    options: Sequence[Mapping[str, JsonValue]] = (),
    kind: CommandType = CommandType.CHAT,
    default_member_permissions: int | None = None,
    nsfw: bool = False,
  ) -> None:
    """Create a command, or change its definition, in a guild (or everywhere).

    Registered with Discord by `CommandSync`; use `option()` to describe options.
    """
    definition: dict[str, JsonValue] = {
      "type": kind,
      "name": _validate_name(name, lower=kind == CommandType.CHAT),
      "nsfw": nsfw,
    }
    if kind == CommandType.CHAT:
      definition["description"] = description
      definition["options"] = [dict(item) for item in options]
    if default_member_permissions is not None:
      definition["default_member_permissions"] = str(default_member_permissions)
    table = await self._storage()
    key = table_key(kind, name)
    while True:
      current = await table.get(key)
      stored = current.value if current else _Stored(definition=definition)
      stored = stored.model_copy(update={"definition": definition})
      if guild_id is None:
        stored.everywhere = True
      elif str(guild_id) not in stored.guilds:
        stored.guilds = [*stored.guilds, str(guild_id)]
      if current is None:
        written = await table.create(key, stored)
      else:
        written = await table.update(key, stored, revision=current.revision)
      if written is not None:
        return

  async def remove(
    self,
    name: str,
    *,
    guild_id: int | str | None = None,
    kind: CommandType = CommandType.CHAT,
  ) -> bool:
    """Remove a command from a guild (or from everywhere); True if it existed."""
    table = await self._storage()
    key = table_key(kind, name)
    while True:
      current = await table.get(key)
      if current is None:
        return False
      stored = current.value
      if guild_id is None:
        stored = stored.model_copy(update={"everywhere": False})
      else:
        stored = stored.model_copy(
          update={"guilds": [g for g in stored.guilds if g != str(guild_id)]}
        )
      if stored.everywhere or stored.guilds:
        if await table.update(key, stored, revision=current.revision) is not None:
          return True
      elif await table.delete(key, revision=current.revision):
        await self._drop_consumer(kind, name)
        return True

  async def commands(self) -> dict[str, dict[str, JsonValue]]:
    """Every runtime command by `type:name`, with its `guild_ids`."""
    return await runtime_definitions(self.service.runtime)

  async def _storage(self) -> Table[_Stored]:
    if self._table is None:
      self._table = await runtime_table(self.service.runtime)
    return self._table

  async def _drop_consumer(self, kind: int, name: str) -> None:
    route = command_route(kind, name)
    for entry in self.service.runtime.directory.entries("service"):
      routes = entry.metadata.get(INTERACTIONS_KEY)
      if isinstance(routes, list) and route in routes:
        return  # a command declared in code shares this consumer
    try:
      await self.service.runtime.jetstream.delete_consumer(
        subjects.INTERACTIONS_STREAM, route_consumer(route)
      )
    except NotFoundError, NatsError:
      pass

  # Serving them ----------------------------------------------------------------

  def routes(self) -> list[str]:
    """The routes of the runtime commands that exist now."""
    return sorted(command_route(kind, name) for kind, name in self._names)

  async def start(self, service: Service) -> None:
    """Serve the existing runtime commands and watch for changes."""
    from micro.discord import DiscordHTTPClient

    self._http = DiscordHTTPClient(service.runtime)
    await ensure_interactions_stream(service)
    table = await self._storage()
    for key in await table.items(PREFIX + ">"):
      await self._serve(key)
    self._watching = service.spawn(self._watch(table), name="runtime-commands")

  async def stop(self) -> None:
    """Stop watching and stop every command's consumer."""
    if self._watching is not None:
      self._watching.cancel()
      await asyncio.gather(self._watching, return_exceptions=True)
      self._watching = None
    running, self._running = self._running, {}
    await asyncio.gather(*(consumer.stop() for consumer in running.values()))

  async def _watch(self, table: Table[_Stored]) -> None:
    failures = 0
    while True:
      # Each watch replays the table; what it no longer holds was removed meanwhile.
      replayed: set[str] | None = set()
      try:
        async for change in table.watch(PREFIX + ">", lenient=True):
          failures = 0
          try:
            if change is None:
              if replayed is not None:
                for kind, name in self._names - {self._parse(k) for k in replayed}:
                  await self._unserve(f"{PREFIX}{kind}.{name}")
                replayed = None
            elif change.error is not None:
              if replayed is not None:
                replayed.add(change.key)  # unreadable, not removed: leave it be
            elif change.value is None:
              await self._unserve(change.key)
            else:
              if replayed is not None:
                replayed.add(change.key)
              await self._serve(change.key)
          except Exception:
            log.exception("Could not update runtime commands")
      except asyncio.CancelledError:
        raise
      except Exception:
        log.warning("The watch on runtime commands failed", exc_info=True)
      failures += 1
      await asyncio.sleep(default_backoff(failures))

  def _parse(self, key: str) -> tuple[int, str]:
    kind, _, name = key.removeprefix(PREFIX).partition(".")
    return int(kind), name

  async def _serve(self, key: str) -> None:
    kind, name = self._parse(key)
    self._names.add((kind, name))
    route = command_route(kind, name)
    if route in self._running:
      return
    consumer = StreamConsumer(
      self.service,
      stream=subjects.INTERACTIONS_STREAM,
      durable=route_consumer(route),
      filters=[subjects.interaction(route)],
      handler=self._deliver,
      concurrency=self.service.concurrency,
      ack_first=True,
      deliver_new=False,
    )
    await consumer.start()
    self._running[route] = consumer

  async def _unserve(self, key: str) -> None:
    kind, name = self._parse(key)
    self._names.discard((kind, name))
    consumer = self._running.pop(command_route(kind, name), None)
    if consumer is not None:
      await consumer.stop()

  def resolve(self, ctx: Interaction) -> Call | None:
    kind = ctx.data.get("type", CommandType.CHAT)
    if (kind, ctx.data.get("name")) not in self._names:
      return None
    if ctx.type == InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE:
      if self._autocomplete is None:
        return None
      function = self._autocomplete
      focused = next(
        (item for item in ctx.data.get("options") or [] if item.get("focused")), {}
      )
      return lambda: self._suggest(ctx, function, focused.get("value"))
    if self._handler is None:
      return None
    function = self._handler
    return lambda: call(function, ctx)

  async def _suggest(
    self, ctx: Interaction, function: Callable[..., Awaitable[Any]], value: Any
  ) -> None:
    choices = await call(function, ctx, value)
    if not ctx.responded:
      await ctx.autocomplete(list(choices or [])[:25])
