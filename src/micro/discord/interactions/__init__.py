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
  ResponseType,
)
from ._custom_id import CUSTOM_ID_LIMIT, CustomId
from ._flow import Flow, Middleware, MiddlewareError, defers
from ._router import RAW_INTERACTION, InteractionRouter
from ._sync import SYNC_LOCK, CommandSync, SyncFailed, sync_commands
from ._templates import (
  INTERACTIONS_KEY,
  RESPONSE_DEADLINE,
  Commands,
  Components,
  InteractionTemplate,
  Modals,
  ensure_interactions_stream,
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
  "Flow",
  "Interaction",
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
  "ResponseType",
  "SyncFailed",
  "defers",
  "ensure_interactions_stream",
  "route_consumer",
  "sync_commands",
)
