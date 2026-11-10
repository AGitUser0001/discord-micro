"""Interaction templates: commands, components, and modals on any service.

    service = Service("tickets")
    commands = Commands(service)

    @commands.slash("ticket", description="Open a ticket")
    async def ticket(ctx: Interaction, topic: str) -> None:
      await ctx.respond(f"Opened {topic}")

Run `InteractionRouter` (routes raw interactions) and `CommandSync` (registers
converged commands) once per deployment, with any number of replicas.
"""

from ._commands import (
  Choice,
  Command,
  CommandGroup,
  CommandOutdated,
  Mentionable,
  Option,
)
from ._context import (
  TOKEN_LIFETIME,
  AlreadyResponded,
  Interaction,
  InteractionExpired,
  InteractionState,
  InvalidResponse,
  Resolved,
  ResponseType,
)
from ._custom_id import CUSTOM_ID_LIMIT, CustomId
from ._endpoint import InteractionEndpoint
from ._flow import Flow, Middleware, MiddlewareError, defers
from ._pattern import PatternRoute, Route
from ._router import RAW_INTERACTION, InteractionRouter
from ._runtime_commands import RuntimeCommands, option
from ._sync import SYNC_LOCK, CommandSync, SyncFailed, sync_commands
from ._templates import (
  INTERACTIONS_KEY,
  RESPONSE_DEADLINE,
  Commands,
  Components,
  ErrorHook,
  InteractionTemplate,
  Modals,
  ensure_interactions_stream,
  report_failure,
  route_consumer,
)

__all__ = (
  "CUSTOM_ID_LIMIT",
  "INTERACTIONS_KEY",
  "RAW_INTERACTION",
  "RESPONSE_DEADLINE",
  "SYNC_LOCK",
  "TOKEN_LIFETIME",
  "AlreadyResponded",
  "Choice",
  "Command",
  "CommandGroup",
  "CommandOutdated",
  "CommandSync",
  "Commands",
  "Components",
  "CustomId",
  "ErrorHook",
  "Flow",
  "Interaction",
  "InteractionEndpoint",
  "InteractionExpired",
  "InteractionRouter",
  "InteractionState",
  "InteractionTemplate",
  "InvalidResponse",
  "Mentionable",
  "Middleware",
  "MiddlewareError",
  "Modals",
  "Option",
  "PatternRoute",
  "Resolved",
  "ResponseType",
  "Route",
  "RuntimeCommands",
  "SyncFailed",
  "defers",
  "ensure_interactions_stream",
  "option",
  "report_failure",
  "route_consumer",
  "sync_commands",
)
