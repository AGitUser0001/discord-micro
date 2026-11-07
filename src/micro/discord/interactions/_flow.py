"""Middleware for interaction flows: `use(fn)` with `fn(ctx, next, end)`.

    @components.use
    async def staff_only(ctx, next, end):
      if not is_staff(ctx.interaction):
        await ctx.interaction.respond("Staff only.", ephemeral=True)
        return await end()
      await next()

Middleware nests in the order it was added; the innermost `next` runs the
template's own handler (the engine is `micro.middleware`). Each pass through a middleware must call exactly one of
`next()`, `end()`, or raise. `use("scope", fn)` limits it to a key and the keys
nested under it (`.` or `:` separated): a command's dotted path such as
`admin.ban`, or a custom ID such as `ticket.close:[42]`.
"""

from collections.abc import Awaitable, Callable, Mapping
from typing import TYPE_CHECKING, Any

from micro.middleware import Middleware, MiddlewareError, Middlewares, Next

from ._context import Interaction

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient
  from micro.service import Service


class Flow:
  """What a middleware sees: one interaction on its way to a handler.

  `payload` is Discord's JSON and may be changed in place (verify or unwrap a
  custom ID, say) before `next()`. `interaction` is the `Interaction` that
  answers it. `state` is scratch space for middleware to share.
  """

  __slots__ = (
    "_http",
    "_interaction",
    "key",
    "payload",
    "reached",
    "received",
    "service",
    "state",
  )

  def __init__(
    self,
    payload: dict[str, Any],
    *,
    http: DiscordHTTPClient,
    key: str | None,
    service: Service | None = None,
    received: float | None = None,
  ) -> None:
    self.payload = payload
    self.key = key
    self.service = service
    self.received = received
    self.state: dict[str, object] = {}
    self.reached = False
    """Whether the flow got all the way to the template's handler."""
    self._http = http
    self._interaction: Interaction | None = None

  @property
  def interaction(self) -> Interaction:
    """The `Interaction` this flow is about."""
    if self._interaction is None:
      self._interaction = Interaction(self.payload, self._http, received=self.received)
    return self._interaction


def flow_key(payload: Mapping[str, Any]) -> str | None:
  """What middleware scopes match: a custom ID, or a command's dotted path."""
  data = payload.get("data")
  if not isinstance(data, Mapping):
    return None
  custom_id = data.get("custom_id")
  if isinstance(custom_id, str):
    return custom_id
  name = data.get("name")
  if not isinstance(name, str):
    return None
  parts = [name]
  options = data.get("options")
  while (
    isinstance(options, list)
    and options
    and isinstance(options[0], Mapping)
    and options[0].get("type") in (1, 2)
  ):
    parts.append(str(options[0].get("name")))
    options = options[0].get("options")
  return ".".join(parts)


def defers(
  *, thinking: bool = False, ephemeral: bool = False
) -> Callable[[Flow, Next], Awaitable[None]]:
  """Middleware that defers before the handler runs (autocomplete is skipped).

  commands.use("admin", defers(ephemeral=True))
  """

  async def defer(ctx: Flow, next: Next) -> None:
    interaction = ctx.interaction
    if not interaction.is_autocomplete:
      await interaction.defer(thinking=thinking, ephemeral=ephemeral)
    await next()

  return defer


__all__ = (
  "Flow",
  "Middleware",
  "MiddlewareError",
  "Middlewares",
  "Next",
  "defers",
  "flow_key",
)
