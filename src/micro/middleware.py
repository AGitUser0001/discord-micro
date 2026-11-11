"""Middleware: `use(fn)` with `fn(ctx, next[, end])`, shared by Service and interactions.

    @service.use
    async def timed(ctx, next):
      started = time.monotonic()
      await next()
      log(ctx.key, time.monotonic() - started)

Middleware nests in the order it was added; the innermost `next` runs the real
handler. Each pass through a middleware must call exactly one of `next()`,
`end()`, or raise. `use("scope", fn)` limits it to a key and the keys nested
under it (`.` or `:` separated).
"""

import inspect
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, overload

from micro.errors import MicroError

type Next = Callable[[], Awaitable[None]]
type Middleware = (
  Callable[[Any, Next], Awaitable[None]]
  | Callable[[Any, Next, Callable[[], Awaitable[None]]], Awaitable[None]]
)


class MiddlewareError(MicroError, RuntimeError):
  """A middleware did not call exactly one of `next()` and `end()`."""


class Scoped(Protocol):
  """What the engine needs of a context: a key to scope on, and a `reached` flag."""

  @property
  def key(self) -> str | None:
    """The key this middleware layer's scope is matched against."""
    ...

  reached: bool


def in_scope(key: str | None, scope: str | None) -> bool:
  """Whether `key` is `scope` or nested under it (separated by `.` or `:`)."""
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


class Middlewares[ContextT: Scoped]:
  """An ordered stack of middleware around a handler."""

  def __init__(self) -> None:
    self._layers: list[_Layer] = []

  @overload
  def use(self, scope: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, function: Middleware, /) -> Middleware: ...
  @overload
  def use(self, scope: str, /) -> Callable[[Middleware], Middleware]: ...

  def use(
    self, scope: Middleware | str, function: Middleware | None = None, /
  ) -> Middleware | Callable[[Middleware], Middleware]:
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

  async def run(
    self, flow: ContextT, final: Callable[[ContextT], Awaitable[None]]
  ) -> None:
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
