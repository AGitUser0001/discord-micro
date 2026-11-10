"""Logging that knows who is calling and what it is part of.

    from micro import log

    log.info("sent report", guild=guild_id, channel=channel_id)
    log.warning("rate limited, retrying in %.1fs", delay, route=route)
    log.error("could not edit", error=error)
    log.exception("handler failed")              # inside an `except`: adds the traceback

    with log.step("archive thread"):             # a named part of the work, timed at DEBUG
      ...

    mine = log.bind(user=user.id)                # a logger that carries these fields
    mine.info("joined")

There is nothing to set up: `log` takes the module it is called from as the logger's
name, so the usual per-module filtering in `logging.config` and `micro run -v` works. It is
the standard `logging` underneath, so every handler and library shares one stream.

A line shows its **fields** and its **path**. Fields are the keyword arguments, anything
bound with `bind`, and anything in scope with `context`. The path is the logical call
path: Micro sets it while a handler runs (`tickets > ticket.close > update_message`), and
`step` adds your own segments. Both live in context variables, so they follow the work
into any task it starts, which a stack of frames cannot do. Both are also kept on the
record (`record.fields`, `record.path`) for a handler that wants JSON.
"""

import inspect
import logging
import sys
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from types import MappingProxyType, TracebackType
from typing import Any, Self, overload

_path: ContextVar[tuple[str, ...]] = ContextVar("micro_log_path", default=())
_fields: ContextVar[Mapping[str, object]] = ContextVar(
  "micro_log_fields", default=MappingProxyType({})
)

type ExcInfo = bool | BaseException | tuple[Any, Any, Any] | None


def path() -> tuple[str, ...]:
  """The logical call path of the work running now, outermost first."""
  return _path.get()


def fields() -> Mapping[str, object]:
  """The fields in scope for the work running now."""
  return _fields.get()


def _render(value: object) -> str:
  text = value if isinstance(value, str) else repr(value)
  return repr(text) if (" " in text or not text) and isinstance(value, str) else text


class Logger:
  """The logger behind `micro.log`. Use the module's `log`, or `bind` it."""

  def __init__(
    self, name: str | None = None, bound: Mapping[str, object] | None = None
  ) -> None:
    self._name = name
    self._bound: Mapping[str, object] = bound or {}

  # Levels ----------------------------------------------------------------------

  def debug(
    self, message: str, *args: object, exc_info: ExcInfo = None, **more: object
  ) -> None:
    """Log at DEBUG: detail for someone chasing a problem."""
    self._emit(logging.DEBUG, message, args, exc_info, more)

  def info(
    self, message: str, *args: object, exc_info: ExcInfo = None, **more: object
  ) -> None:
    """Log at INFO: something normal worth a line."""
    self._emit(logging.INFO, message, args, exc_info, more)

  def warning(
    self, message: str, *args: object, exc_info: ExcInfo = None, **more: object
  ) -> None:
    """Log at WARNING: something unexpected that was dealt with."""
    self._emit(logging.WARNING, message, args, exc_info, more)

  def error(
    self, message: str, *args: object, exc_info: ExcInfo = None, **more: object
  ) -> None:
    """Log at ERROR: something failed."""
    self._emit(logging.ERROR, message, args, exc_info, more)

  def critical(
    self, message: str, *args: object, exc_info: ExcInfo = None, **more: object
  ) -> None:
    """Log at CRITICAL: the process cannot carry on."""
    self._emit(logging.CRITICAL, message, args, exc_info, more)

  def exception(self, message: str, *args: object, **more: object) -> None:
    """Log at ERROR with the exception being handled (call it inside `except`)."""
    self._emit(logging.ERROR, message, args, True, more)

  def log(
    self,
    level: int,
    message: str,
    *args: object,
    exc_info: ExcInfo = None,
    **more: object,
  ) -> None:
    """Log at a level given as a number."""
    self._emit(level, message, args, exc_info, more)

  def enabled(self, level: int = logging.DEBUG) -> bool:
    """Whether a line at `level` would be written (to skip building an expensive one)."""
    return self._logger(2).isEnabledFor(level)

  # Fields and path -----------------------------------------------------------------

  def bind(self, **more: object) -> Logger:
    """A logger carrying these fields on every line (and the ones already bound)."""
    return Logger(self._name, {**self._bound, **more})

  @contextmanager
  def context(self, **more: object) -> Iterator[None]:
    """Put fields on every line logged meanwhile, by this work and any task it starts."""
    token = _fields.set({**_fields.get(), **more})
    try:
      yield
    finally:
      _fields.reset(token)

  def step(self, name: str) -> Span:
    """A named part of the work: it joins the path while it runs.

        with log.step("archive thread"): ...        # also async with
        @log.step("archive thread")                 # also on an async function

    How long it took is logged at DEBUG when it ends, and `failed` if it raised.
    """
    return Span(Logger(self._logger(2).name, self._bound), name)

  # Internals -------------------------------------------------------------------

  def _logger(self, depth: int) -> logging.Logger:
    if self._name is not None:
      return logging.getLogger(self._name)
    name = sys._getframe(depth).f_globals.get("__name__", "micro")  # pyright: ignore[reportPrivateUsage]
    return logging.getLogger(name if isinstance(name, str) else "micro")

  def _emit(
    self,
    level: int,
    message: str,
    args: tuple[object, ...],
    exc_info: ExcInfo,
    more: Mapping[str, object],
  ) -> None:
    logger = self._logger(3)
    if not logger.isEnabledFor(level):
      return
    merged = {**_fields.get(), **self._bound, **more}
    where = _path.get()
    suffix = ""
    if where:
      suffix += f"  path={' > '.join(where)}"
    if merged:
      suffix += "  " + " ".join(f"{k}={_render(v)}" for k, v in merged.items())
    if args:
      suffix = suffix.replace("%", "%%")  # the message is %-formatted with `args`
    logger.log(
      level,
      message + suffix,
      *args,
      exc_info=exc_info,
      stacklevel=3,
      extra={"fields": merged, "path": where},
    )


class Span:
  """A `Logger.step`: a context manager (sync or async) and a decorator."""

  def __init__(self, logger: Logger, name: str) -> None:
    self._logger = logger
    self._name = name
    self._tokens: list[tuple[object, float]] = []

  def __enter__(self) -> Self:
    self._tokens.append((_path.set((*_path.get(), self._name)), perf_counter()))
    return self

  def __exit__(
    self,
    kind: type[BaseException] | None,
    error: BaseException | None,
    traceback: TracebackType | None,
  ) -> None:
    token, started = self._tokens.pop()
    seconds = perf_counter() - started
    outcome = "failed" if error is not None else "done"
    self._logger.debug("%s %s in %.1f ms", self._name, outcome, seconds * 1000)
    _path.reset(token)  # pyright: ignore[reportArgumentType]

  async def __aenter__(self) -> Self:
    return self.__enter__()

  async def __aexit__(
    self,
    kind: type[BaseException] | None,
    error: BaseException | None,
    traceback: TracebackType | None,
  ) -> None:
    self.__exit__(kind, error, traceback)

  @overload
  def __call__[**P, R](self, function: Callable[P, R]) -> Callable[P, R]: ...
  @overload
  def __call__(self, function: Any) -> Any: ...

  def __call__(self, function: Any) -> Any:
    if inspect.iscoroutinefunction(function):

      async def awaited(*args: Any, **kwargs: Any) -> Any:
        with Span(self._logger, self._name):
          return await function(*args, **kwargs)

      return _wrap(awaited, function)

    def called(*args: Any, **kwargs: Any) -> Any:
      with Span(self._logger, self._name):
        return function(*args, **kwargs)

    return _wrap(called, function)


def _wrap(wrapper: Any, function: Any) -> Any:
  import functools

  return functools.wraps(function)(wrapper)


_default = Logger()

debug = _default.debug
info = _default.info
warning = _default.warning
error = _default.error
critical = _default.critical
exception = _default.exception
log = _default.log
enabled = _default.enabled
bind = _default.bind
context = _default.context
step = _default.step

__all__ = (
  "Logger",
  "Span",
  "bind",
  "context",
  "critical",
  "debug",
  "enabled",
  "error",
  "exception",
  "fields",
  "info",
  "log",
  "path",
  "step",
  "warning",
)
