"""Interaction templates: attach to any service, shape them with middleware."""

import asyncio
import json
import re
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypedDict, Unpack, overload

from nats.aio.msg import Msg
from nats.js.api import RetentionPolicy
from pydantic import JsonValue

from micro import log, subjects
from micro._handling import handling
from micro.discord.objects import Member, Message, User
from micro.discord.routes import (
  AUTOCOMPLETE,
  MESSAGE,
  SLASH,
  USER,
  command_route,
  component_route,
  modal_route,
)
from micro.discord.ui import Draft
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
from ._pattern import Route, as_route, route_id, wire_of

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient
  from micro.service import Service

INTERACTIONS_KEY = "interactions"
"""Presence metadata: the interaction routes a service handles."""

RESPONSE_DEADLINE = 3
"""Seconds Discord allows for an interaction's initial response."""

LATE_WARNING = 2.0
"""Seconds into Discord's deadline after which a late interaction is worth a warning."""

type Call = Callable[[], Awaitable[Any]]

type ErrorHook = Callable[[Flow, BaseException], Awaitable[None]]
"""`async def hook(flow, error)`: what to do when an interaction's handler or middleware
raised. It runs after the error is logged and may answer `flow.interaction` as it likes."""


class MenuSettings(TypedDict, total=False):
  """Options of a `user` or `message` context-menu command."""

  guild_ids: Sequence[int]
  default_member_permissions: int | None
  contexts: tuple[int, ...] | None
  integration_types: tuple[int, ...] | None
  nsfw: bool
  name_localizations: Mapping[str, str] | None


async def ensure_interactions_stream(service: Service) -> None:
  """Create the `MICRO_INTERACTIONS` work-queue stream if needed."""
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
    self._middleware: Middlewares[Flow] = Middlewares()
    self._on_error: ErrorHook = report_failure
    service.extend(self)

  # Subclasses describe their routes and how to run one interaction.

  def routes(self) -> list[str]:
    """The routes this template handles (override in a subclass)."""
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

  def use(
    self, scope: Middleware | str, function: Middleware | None = None, /
  ) -> Middleware | Callable[[Middleware], Middleware]:
    """Add middleware around every handler: `use(fn)`, `use("scope", fn)`."""
    if function is None:
      return self._middleware.use(scope)  # type: ignore[arg-type]
    return self._middleware.use(scope, function)  # type: ignore[arg-type]

  def on_error(self, hook: ErrorHook) -> ErrorHook:
    """Decide what happens when a handler or its middleware raises (a decorator).

        @commands.on_error
        async def failed(flow: Flow, error: BaseException) -> None:
          if isinstance(error, PermissionError):
            await flow.interaction.respond(Draft("Not allowed.", ephemeral=True))

    The error is always logged first. The default, `report_failure`, answers with an
    ephemeral "Something went wrong."; your hook replaces it entirely (answer however
    you like, or not at all). One hook per template; a second call replaces the first.
    """
    self._on_error = hook
    return hook

  # ServiceExtension.

  def metadata(self) -> dict[str, JsonValue]:
    """What the service advertises: the routes it handles."""
    routes: list[JsonValue] = [*self.routes()]
    return {INTERACTIONS_KEY: routes}

  async def start(self, service: Service) -> None:
    """Start one durable consumer per route."""
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
    """Stop the consumers, waiting for running handlers."""
    consumers, self._consumers = self._consumers, []
    await asyncio.gather(*(consumer.stop() for consumer in consumers))

  @property
  def http(self) -> DiscordHTTPClient:
    """The HTTP client used to answer interactions (set once started)."""
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
    age = flow.interaction.age
    if age > LATE_WARNING:
      log.warning(
        "Interaction %s reached a handler %.1f s after Discord created it "
        "(Discord allows %d s to answer); the delay is before the handler "
        "(gateway, NATS, or this machine's clock).",
        flow.interaction.id,
        age,
        RESPONSE_DEADLINE,
      )
    await self.handle(flow)

  async def handle(self, flow: Flow) -> None:
    """Run one interaction through the middleware and the template's handler."""
    try:
      with handling(
        self.service.name, f"interaction {flow.key}", interaction=flow.interaction.id
      ):
        await self._middleware.run(flow, self._dispatch)
    except Exception as error:
      log.exception(
        "Interaction handler failed in %s (%.1f s after Discord created it)",
        self.service.name,
        flow.interaction.age,
      )
      await run_error_hook(self._on_error, flow, error)
      return
    if not flow.reached and not flow.interaction.responded:
      log.warning(
        "Middleware ended %r without responding; Discord will show a failure.",
        flow.key,
      )

  async def _dispatch(self, flow: Flow) -> None:
    call = self.resolve(flow.interaction)
    if call is None:
      log.warning("%s received an interaction it does not handle", type(self).__name__)
      return
    await call()


async def run_error_hook(hook: ErrorHook, flow: Flow, error: BaseException) -> None:
  """Call an error hook; one that itself fails is logged and does nothing more."""
  try:
    await hook(flow, error)
  except Exception:
    log.warning("The interaction error hook failed", exc_info=True)


async def report_failure(flow: Flow, error: BaseException) -> None:
  """The default error hook: tell the user, in an ephemeral reply, that it failed."""
  try:
    interaction = flow.interaction
    if interaction.expired or interaction.is_autocomplete:
      return
    if isinstance(error, CommandOutdated):
      text = "This command was just updated. Please try again."
    else:
      text = "Something went wrong."
    await interaction.respond(Draft(text, ephemeral=True))
  except Exception:
    log.warning("Could not report an interaction error", exc_info=True)


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

  def user(
    self, name: str, **settings: Unpack[MenuSettings]
  ) -> Callable[[Handler], Command]:
    """A context-menu command on users: `async def f(ctx, member: Member)`."""
    return self._context_menu(USER, name, settings)

  def message(
    self, name: str, **settings: Unpack[MenuSettings]
  ) -> Callable[[Handler], Command]:
    """A context-menu command on messages: `async def f(ctx, message: Message)`."""
    return self._context_menu(MESSAGE, name, settings)

  def _context_menu(
    self, kind: int, name: str, settings: MenuSettings
  ) -> Callable[[Handler], Command]:
    def register(handler: Handler) -> Command:
      _require_async(handler)
      command = Command(
        name,
        handler,
        "",
        kind,
        guild_ids=tuple(settings.get("guild_ids", self.guild_ids)),
        default_member_permissions=settings.get("default_member_permissions"),
        contexts=settings.get("contexts"),
        integration_types=settings.get("integration_types"),
        nsfw=settings.get("nsfw", False),
        name_localizations=settings.get("name_localizations"),
      )
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
    """Every command and group declared here."""
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
    """The routes (one per command name) this template handles."""
    return sorted(command_route(kind, name) for kind, name in self._commands)

  async def start(self, service: Service) -> None:
    # Declared at start so autocomplete flags added after declaration count.
    """Declare the commands for `CommandSync` and start a consumer per route."""
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
  _patterns_key = "component_patterns"

  def __init__(self, service: Service) -> None:
    super().__init__(service)
    self._matchers: dict[str, tuple[Route, Handler]] = {}

  def match(
    self, route: Route | str | re.Pattern[str], *, prefix: str | None = None
  ) -> Callable[[Handler], Handler]:
    """Handle every custom_id a route matches (see `Route`, `PatternRoute`).

    A `CustomId` owns its prefix (before the first ':') and hands its decoded
    state to `async def f(ctx, state)`. A plain string owns that prefix and
    what is nested under it (`.` or `:`); with `{name}` placeholders it is a
    template. A compiled regex is used as is (`prefix=` sets its literal head
    if it cannot be derived). Otherwise the handler is `async def f(ctx)` and
    the route's result is `ctx.route`.
    """
    declared = as_route(route, prefix)

    def register(handler: Handler) -> Handler:
      _require_async(handler)
      queue = self._route(route_id(declared))
      if queue in self._matchers:
        raise ValueError(f"Route {declared!r} is already handled here.")
      self._matchers[queue] = (declared, handler)
      return handler

    return register

  def routes(self) -> list[str]:
    return sorted(self._matchers)

  def metadata(self) -> dict[str, JsonValue]:
    metadata = super().metadata()
    if self._matchers:
      declared: dict[str, JsonValue] = {
        queue: wire_of(route) for queue, (route, _) in self._matchers.items()
      }
      metadata[self._patterns_key] = declared
    return metadata

  def resolve(self, ctx: Interaction) -> Call | None:
    custom_id = ctx.custom_id or ""
    for route, handler in sorted(
      self._matchers.values(), key=lambda entry: -len(entry[0].prefix)
    ):
      params = route.match(custom_id)
      if params is None:
        continue
      ctx.route = params
      if isinstance(route, CustomId) and route.state is not None:
        state = route.decode(custom_id)
        return lambda handler=handler: handler(ctx, state)
      return lambda handler=handler: handler(ctx)
    return None


class Components(_CustomIdTemplate):
  """Buttons and select menus, routed by custom ID: `@components.match(VOTE)`."""

  _route = staticmethod(component_route)


class Modals(_CustomIdTemplate):
  """Modal submissions, routed by custom ID: `@modals.match(FEEDBACK)`."""

  _route = staticmethod(modal_route)
  _patterns_key = "modal_patterns"
