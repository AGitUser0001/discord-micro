"""Interaction templates: attach to any service, shape them with middleware."""

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, overload

from nats.aio.msg import Msg
from nats.js.api import RetentionPolicy
from pydantic import JsonValue

from micro import subjects
from micro.discord.objects import Member, Message, User
from micro.discord.routes import (
  AUTOCOMPLETE,
  MESSAGE,
  SLASH,
  USER,
  command_route,
  component_route,
  custom_id_prefix,
  modal_route,
)
from micro.runtime import StreamConsumer

from ._commands import (
  Command,
  CommandGroup,
  CommandOutdated,
  Handler,
  _require_async,
  _validate_name,
  convert_options,
  parse_options,
)
from ._context import Interaction
from ._custom_id import CustomId
from ._flow import Flow, Middleware, Middlewares, flow_key

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient
  from micro.service import Service

logger = logging.getLogger("micro")

INTERACTIONS_KEY = "interactions"
"""Presence metadata: the interaction routes a service handles."""

RESPONSE_DEADLINE = 3
"""Seconds Discord allows for an interaction's initial response."""

type Call = Callable[[], Awaitable[Any]]


async def ensure_interactions_stream(service: Service) -> None:
  await service.runtime.ensure_stream(
    subjects.INTERACTIONS_STREAM,
    subjects.INTERACTION_SUBJECTS,
    retention=RetentionPolicy.WORK_QUEUE,
    allow_msg_ttl=True,
  )


def route_consumer(route: str) -> str:
  """The one durable consumer shared by every worker of a route."""
  return subjects.durable("ix", route)


class InteractionTemplate:
  """Base for templates that handle routed interactions.

  Each route gets one durable consumer on the interactions work queue, shared
  by every replica and version of every service handling it; all of them pull
  from it. Shape what happens around a handler with `use` (see `_flow`):
  authorization, cooldowns, logging, deferral (`defers()`), unwrapping signed
  custom IDs, or a custom error reply. Nothing is deferred automatically.
  """

  def __init__(self, service: Service) -> None:
    self.service = service
    self._consumers: list[StreamConsumer] = []
    self._http: DiscordHTTPClient | None = None
    self._middleware = Middlewares()
    service.extend(self)

  # Subclasses describe their routes and how to run one interaction.

  def routes(self) -> list[str]:
    raise NotImplementedError

  def resolve(self, ctx: Interaction) -> Call | None:
    """The call handling this interaction, or None if this template has none."""
    raise NotImplementedError

  @overload
  def use(self, scope: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, function: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, /) -> Callable[[Middleware], Middleware]: ...

  def use(self, scope: Middleware | str, function: Middleware | None = None, /) -> Any:
    """Add middleware around every handler: `use(fn)`, `use("scope", fn)`."""
    if function is None:
      return self._middleware.use(scope)  # type: ignore[arg-type]
    return self._middleware.use(scope, function)  # type: ignore[arg-type]

  # ServiceExtension.

  def metadata(self) -> dict[str, JsonValue]:
    routes: list[JsonValue] = [*self.routes()]
    return {INTERACTIONS_KEY: routes}

  async def start(self, service: Service) -> None:
    from micro.discord import DiscordHTTPClient

    self._http = DiscordHTTPClient(service.runtime)
    routes = self.routes()
    if not routes:
      return
    await ensure_interactions_stream(service)
    for route in routes:
      consumer = StreamConsumer(
        service,
        stream=subjects.INTERACTIONS_STREAM,
        durable=route_consumer(route),
        filters=[subjects.interaction(route)],
        handler=self._deliver,
        concurrency=service.concurrency,
        ack_first=True,
        deliver_new=False,
      )
      await consumer.start()
      self._consumers.append(consumer)

  async def stop(self) -> None:
    consumers, self._consumers = self._consumers, []
    await asyncio.gather(*(consumer.stop() for consumer in consumers))

  @property
  def http(self) -> DiscordHTTPClient:
    if self._http is None:
      raise RuntimeError("The template's service has not started.")
    return self._http

  async def _deliver(self, message: Msg) -> None:
    payload = json.loads(message.data)
    flow = Flow(
      payload,
      http=self.http,
      key=flow_key(payload),
      service=self.service,
      received=time.monotonic(),
    )
    await self.handle(flow)

  async def handle(self, flow: Flow) -> None:
    """Run one interaction through the middleware and the template's handler."""
    try:
      await self._middleware.run(flow, self._dispatch)
    except Exception as error:
      logger.exception("Interaction handler failed in %s", self.service.name)
      await report_failure(flow, error)
      return
    if not flow.reached and not flow.interaction.responded:
      logger.warning(
        "Middleware ended %r without responding; Discord will show a failure.",
        flow.key,
      )

  async def _dispatch(self, flow: Flow) -> None:
    call = self.resolve(flow.interaction)
    if call is None:
      logger.warning(
        "%s received an interaction it does not handle", type(self).__name__
      )
      return
    await call()


async def report_failure(flow: Flow, error: BaseException) -> None:
  """Tell the user a handler or middleware failed (the default error layer)."""
  try:
    interaction = flow.interaction
    if interaction.expired or interaction.is_autocomplete:
      return
    if isinstance(error, CommandOutdated):
      text = "This command was just updated. Please try again."
    else:
      text = "Something went wrong."
    await interaction.respond(text, ephemeral=True)
  except Exception:
    logger.warning("Could not report an interaction error", exc_info=True)


class Commands(InteractionTemplate):
  """Slash, user, and message commands declared from typed functions.

      commands = Commands(service)

      @commands.slash("ticket", description="Open a ticket")
      async def ticket(ctx: Interaction, topic: str, urgent: bool = False) -> None: ...

  Definitions are declared, not synced: run one `CommandSync` component, which
  registers a new definition once every live replica agrees on it.
  """

  def __init__(
    self,
    service: Service,
    *,
    guild_ids: Sequence[int] = (),
  ) -> None:
    super().__init__(service)
    self.guild_ids = tuple(guild_ids)
    self._commands: dict[tuple[int, str], Command | CommandGroup] = {}

  def slash(
    self,
    name: str,
    *,
    description: str = "-",
    guild_ids: Sequence[int] | None = None,
    default_member_permissions: int | None = None,
    contexts: Sequence[int] | None = None,
    integration_types: Sequence[int] | None = None,
    nsfw: bool = False,
    name_localizations: Mapping[str, str] | None = None,
    description_localizations: Mapping[str, str] | None = None,
  ) -> Callable[[Handler], Command]:
    """Declare a slash command; options come from the handler's parameters."""

    def register(handler: Handler) -> Command:
      _require_async(handler)
      command = Command(
        _validate_name(name),
        handler,
        description,
        SLASH,
        parse_options(handler),
        guild_ids=tuple(guild_ids) if guild_ids is not None else self.guild_ids,
        default_member_permissions=default_member_permissions,
        contexts=tuple(contexts) if contexts is not None else None,
        integration_types=tuple(integration_types)
        if integration_types is not None
        else None,
        nsfw=nsfw,
        name_localizations=name_localizations,
        description_localizations=description_localizations,
      )
      self._add(command)
      return command

    return register

  def group(
    self,
    name: str,
    *,
    description: str = "-",
    guild_ids: Sequence[int] | None = None,
    default_member_permissions: int | None = None,
    contexts: Sequence[int] | None = None,
    integration_types: Sequence[int] | None = None,
    nsfw: bool = False,
  ) -> CommandGroup:
    """A slash command whose subcommands are added with `.command(...)`."""
    group = CommandGroup(
      _validate_name(name),
      description,
      guild_ids=tuple(guild_ids) if guild_ids is not None else self.guild_ids,
      default_member_permissions=default_member_permissions,
      contexts=tuple(contexts) if contexts is not None else None,
      integration_types=tuple(integration_types)
      if integration_types is not None
      else None,
      nsfw=nsfw,
    )
    self._add(group)
    return group

  def user(self, name: str, **settings: Any) -> Callable[[Handler], Command]:
    """A context-menu command on users: `async def f(ctx, member: Member)`."""
    return self._context_menu(USER, name, settings)

  def message(self, name: str, **settings: Any) -> Callable[[Handler], Command]:
    """A context-menu command on messages: `async def f(ctx, message: Message)`."""
    return self._context_menu(MESSAGE, name, settings)

  def _context_menu(
    self, kind: int, name: str, settings: dict[str, Any]
  ) -> Callable[[Handler], Command]:
    def register(handler: Handler) -> Command:
      _require_async(handler)
      guild_ids = tuple(settings.pop("guild_ids", self.guild_ids))
      command = Command(name, handler, "", kind, guild_ids=guild_ids, **settings)
      self._add(command)
      return command

    return register

  def _add(self, command: Command | CommandGroup) -> None:
    key = (command.type, command.name)
    if key in self._commands:
      raise ValueError(f"Command {command.name!r} is already declared here.")
    self._commands[key] = command

  @property
  def commands(self) -> tuple[Command | CommandGroup, ...]:
    return tuple(self._commands.values())

  def definitions(self) -> dict[str, JsonValue]:
    """Each command's Discord definition, keyed `type:name`."""
    definitions: dict[str, JsonValue] = {}
    for (kind, name), command in self._commands.items():
      value = command.to_dict()
      value["guild_ids"] = [str(guild) for guild in command.guild_ids]
      definitions[f"{kind}:{name}"] = value
    return definitions

  def routes(self) -> list[str]:
    return sorted(command_route(kind, name) for kind, name in self._commands)

  async def start(self, service: Service) -> None:
    # Declared at start so autocomplete flags added after declaration count.
    for key, definition in self.definitions().items():
      service.declare("commands", key, definition)
    await super().start(service)

  def _find(self, ctx: Interaction) -> tuple[Command, list[dict[str, Any]]] | None:
    data = ctx.data
    declared = self._commands.get((data.get("type", SLASH), data.get("name", "")))
    if declared is None:
      return None
    options: list[dict[str, Any]] = list(data.get("options") or [])
    if isinstance(declared, CommandGroup):
      try:
        return declared.resolve(options)
      except LookupError as error:
        raise CommandOutdated(str(error)) from error
    return declared, options

  def resolve(self, ctx: Interaction) -> Call | None:
    found = self._find(ctx)
    if found is None:
      return None
    command, options = found
    if ctx.type == AUTOCOMPLETE:
      return lambda: self._autocomplete(ctx, command, options)
    return lambda: self._invoke(ctx, command, options)

  async def _invoke(
    self, ctx: Interaction, command: Command, options: list[dict[str, Any]]
  ) -> None:
    resolved = ctx.data.get("resolved") or {}
    if command.type == SLASH:
      await command.handler(ctx, **convert_options(command.options, options, resolved))
      return
    target = ctx.data.get("target_id")
    if command.type == USER:
      users = resolved.get("users") or {}
      members = resolved.get("members") or {}
      if target in members:
        member = Member.model_validate({**members[target], "user": users.get(target)})
        await command.handler(ctx, member)
      else:
        await command.handler(
          ctx, User.model_validate(users.get(target, {"id": target}))
        )
      return
    messages = resolved.get("messages") or {}
    message = messages.get(target, {"id": target, "channel_id": ctx.channel_id})
    await command.handler(ctx, Message.model_validate(message))

  async def _autocomplete(
    self, ctx: Interaction, command: Command, options: list[dict[str, Any]]
  ) -> None:
    focused = next((item for item in options if item.get("focused")), None)
    handler = command.autocompleters.get(focused.get("name", "")) if focused else None
    choices = await handler(ctx, focused.get("value")) if handler and focused else []
    if not ctx.responded:
      await ctx.autocomplete(list(choices or [])[:25])


class _CustomIdTemplate(InteractionTemplate):
  _route: Callable[[str], str] = staticmethod(component_route)

  def __init__(self, service: Service) -> None:
    super().__init__(service)
    self._handlers: dict[str, tuple[CustomId[Any] | None, Handler]] = {}

  def on(self, custom_id: CustomId[Any] | str) -> Callable[[Handler], Handler]:
    """Handle every custom_id with this prefix.

    The handler is `async def f(ctx)`, or `async def f(ctx, state)` for a
    stateful `CustomId`.
    """
    codec = custom_id if isinstance(custom_id, CustomId) else None
    prefix = custom_id.prefix if isinstance(custom_id, CustomId) else custom_id

    def register(handler: Handler) -> Handler:
      _require_async(handler)
      if prefix in self._handlers:
        raise ValueError(f"custom_id prefix {prefix!r} is already handled here.")
      self._handlers[prefix] = (codec, handler)
      return handler

    return register

  def routes(self) -> list[str]:
    return sorted(self._route(prefix) for prefix in self._handlers)

  def resolve(self, ctx: Interaction) -> Call | None:
    custom_id = ctx.custom_id or ""
    entry = self._handlers.get(custom_id_prefix(custom_id))
    if entry is None:
      return None
    codec, handler = entry
    if codec is not None and codec.state is not None:
      state = codec.decode(custom_id)
      return lambda: handler(ctx, state)
    return lambda: handler(ctx)


class Components(_CustomIdTemplate):
  """Buttons and select menus, owned by custom_id prefix: `@components.on(VOTE)`."""

  _route = staticmethod(component_route)


class Modals(_CustomIdTemplate):
  """Modal submissions, owned by custom_id prefix: `@modals.on(FEEDBACK)`."""

  _route = staticmethod(modal_route)
