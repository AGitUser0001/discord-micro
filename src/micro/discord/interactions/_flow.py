"""Middleware for interaction flows: `use(fn)` with `fn(ctx, next, end)`.

    @components.use
    async def staff_only(ctx, next, end):
      if not is_staff(ctx.interaction):
        await ctx.interaction.respond("Staff only.", ephemeral=True)
        return await end()
      await next()

Middleware nests in the order it was added; the innermost `next` runs the
template's own handler. Each pass through a middleware must call exactly one of
`next()`, `end()`, or raise. `use("scope", fn)` limits it to a key and the keys
nested under it (`.` or `:` separated): a command's dotted path such as
`admin.ban`, or a custom ID such as `ticket.close:[42]`.
"""

import inspect
from collections.abc import Awaitable, Callable, Mapping
from typing import TYPE_CHECKING, Any, overload

from micro.errors import MicroError

from ._context import Interaction

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient
  from micro.service import Service

type Next = Callable[[], Awaitable[None]]
type Middleware = Callable[..., Awaitable[None]]


class MiddlewareError(MicroError, RuntimeError):
  """A middleware did not call exactly one of `next()` and `end()`."""


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
    self.state: dict[str, Any] = {}
    self.reached = False
    """Whether the flow got all the way to the template's handler."""
    self._http = http
    self._interaction: Interaction | None = None

  @property
  def interaction(self) -> Interaction:
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


def in_scope(key: str | None, scope: str | None) -> bool:
  if scope is None:
    return True
  if key is None or not key.startswith(scope):
    return False
  return len(key) == len(scope) or key[len(scope)] in ".:"


class _Layer:
  __slots__ = ("function", "name", "scope", "takes_end")

  def __init__(self, scope: str | None, function: Middleware) -> None:
    if not inspect.iscoroutinefunction(function):
      raise TypeError("Middleware must be `async def f(ctx, next[, end])`.")
    parameters = inspect.signature(function).parameters.values()
    count = sum(
      1
      for item in parameters
      if item.kind in (item.POSITIONAL_ONLY, item.POSITIONAL_OR_KEYWORD)
    )
    variadic = any(item.kind is item.VAR_POSITIONAL for item in parameters)
    if not (count in (2, 3) or variadic):
      raise TypeError("Middleware takes (ctx, next) or (ctx, next, end).")
    self.scope = scope
    self.function = function
    self.takes_end = count == 3 or variadic
    self.name = getattr(function, "__qualname__", repr(function))


class Middlewares:
  """An ordered stack of middleware around a template's handler."""

  def __init__(self) -> None:
    self._layers: list[_Layer] = []

  @overload
  def use(self, scope: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, function: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, /) -> Callable[[Middleware], Middleware]: ...

  def use(self, scope: Middleware | str, function: Middleware | None = None, /) -> Any:
    """Add middleware: `use(fn)`, `use("scope", fn)`, or as a decorator."""
    if not isinstance(scope, str):
      self._layers.append(_Layer(None, scope))
      return scope
    if function is None:

      def register(inner: Middleware) -> Middleware:
        self._layers.append(_Layer(scope, inner))
        return inner

      return register
    self._layers.append(_Layer(scope, function))
    return function

  @property
  def active(self) -> list[str]:
    """The stack in order, for logging."""
    return [
      f"{layer.scope}: {layer.name}" if layer.scope else layer.name
      for layer in self._layers
    ]

  async def run(self, flow: Flow, final: Callable[[Flow], Awaitable[None]]) -> None:
    """Run the flow through every matching middleware, then `final`."""
    layers = [layer for layer in self._layers if in_scope(flow.key, layer.scope)]

    async def step(index: int) -> None:
      if index == len(layers):
        flow.reached = True
        await final(flow)
        return
      layer = layers[index]
      settled: list[str] = []

      def settle(what: str) -> None:
        if settled:
          raise MiddlewareError(
            f"{layer.name} called {settled[0]} and then {what}; call exactly one."
          )
        settled.append(what)

      async def next_() -> None:
        settle("next()")
        await step(index + 1)

      async def end() -> None:
        settle("end()")

      if layer.takes_end:
        await layer.function(flow, next_, end)
      else:
        await layer.function(flow, next_)
      if not settled:
        raise MiddlewareError(f"{layer.name} returned without calling next() or end().")

    await step(0)


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
