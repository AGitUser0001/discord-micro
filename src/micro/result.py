"""Results: a call that can fail in an expected way returns its outcome as a value.

    match await message.edit(content="hi"):
      case Ok(edited): ...
      case Err(NotFound()): ...            # it was deleted meanwhile
      case Err(error): raise error

    text = (await channel.send("hi")).unwrap()         # abort: the error is raised
    sent = (await channel.send("hi")).ok()              # the message, or None
    (await message.delete()).ignore(NotFound)           # only "already gone" is fine

A `Result[T, E]` is an `Ok` holding the `T` or an `Err` holding the `E`. Handle it where
you need to (`match`, `ok()`, `unwrap_or(default)`) or pass it on as a failure with
`unwrap()`, which raises the original error so the generic handler sees it unchanged.
Failures that are bugs or broken infrastructure (a bad argument, NATS down) are not
results: they raise, as ever.

**An `Err` nobody looked at is reported.** Dropping a result on the floor
(`await message.delete()` on a line of its own) would hide a failure that an exception
could not. So an `Err` counts as *looked at* once you use it in any way (`unwrap`, `ok`,
`unwrap_or`, `ignore`, `map`, `is_ok`/`is_err`, or read `.error`, which is what `match`
does) and one that is not is reported twice over:

* while a handler runs (`handling`, which Micro wraps around every handler), a result left
  unlooked-at when the handler finishes raises `UnhandledResult` from it, so the handler
  fails the way it would have with an exception: logged with the original error and
  where the result was created, "Something went wrong" for an interaction, a retry for
  an event;
* anywhere else (a script, a task nobody awaits) it is logged at ERROR when the `Err`
  is garbage collected, with the same details, because nothing can be raised from there.
"""

import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Literal, NoReturn, final

from micro import log
from micro.errors import MicroError


@dataclass(frozen=True, slots=True)
class Ok[T]:
  """The call worked; `value` is what it returned."""

  value: T

  @property
  def is_ok(self) -> Literal[True]:
    """True: the call worked."""
    return True

  @property
  def is_err(self) -> Literal[False]:
    """False: the call worked."""
    return False

  def ok(self) -> T:
    """The value (an `Err` gives None here)."""
    return self.value

  def unwrap(self) -> T:
    """The value (an `Err` raises its error here)."""
    return self.value

  def unwrap_or[D](self, default: D) -> T | D:
    """The value, or `default` for an `Err`."""
    return self.value

  def ignore(self, *errors: type[Exception]) -> T | None:
    """The value; for an `Err` of one of `errors` None, and any other error raised."""
    return self.value

  def map[U](self, function: Callable[[T], U]) -> Ok[U]:
    """An `Ok` of `function(value)`; an `Err` stays as it is."""
    return Ok(function(self.value))


type _Frame = tuple[str, int, str]
"""A stack frame as `(file, line, function)`."""


class UnhandledResult(MicroError):
  """A handler finished while an `Err` it created had never been looked at."""

  def __init__(self, unhandled: list[Err[Exception]]) -> None:
    self.unhandled = unhandled
    lines = [f"{len(unhandled)} error result(s) were never looked at:"]
    lines += [f"  {item._describe()}" for item in unhandled]  # pyright: ignore[reportPrivateUsage]
    lines.append(
      "Handle them (match / ok() / unwrap_or()), or write .unwrap() to let them fail."
    )
    super().__init__("\n".join(lines))


_scope: ContextVar[list[Err[Exception]] | None] = ContextVar(
  "micro_result_scope", default=None
)


@final
class Err[E: Exception]:
  """The call failed in an expected way; `error` says how.

  Reading `error` (which `match` does), or any method here, marks it as looked at.
  """

  __slots__ = ("__weakref__", "_error", "_looked", "_made", "_reported")
  __match_args__ = ("error",)

  def __init__(self, error: E) -> None:
    self._error = error
    self._looked = False
    self._reported = False
    self._made: tuple[_Frame, ...] = _stack()
    scope = _scope.get()
    if scope is not None:
      scope.append(self)  # pyright: ignore[reportArgumentType]

  @property
  def error(self) -> E:
    """The error."""
    self._looked = True
    return self._error

  @property
  def is_ok(self) -> Literal[False]:
    """False: the call failed."""
    self._looked = True
    return False

  @property
  def is_err(self) -> Literal[True]:
    """True: the call failed."""
    self._looked = True
    return True

  def ok(self) -> None:
    """None, as there is no value (an `Ok` gives its value here)."""
    self._looked = True

  def unwrap(self) -> NoReturn:
    """Raise the error (an `Ok` gives its value here)."""
    self._looked = True
    raise self._error

  def unwrap_or[D](self, default: D) -> D:
    """`default`, as there is no value (an `Ok` gives its value here)."""
    self._looked = True
    return default

  def ignore(self, *errors: type[Exception]) -> None:
    """None if the error is one of `errors`; any other error is raised."""
    self._looked = True
    if isinstance(self._error, errors):
      return
    raise self._error

  def map[U](self, function: Callable[[object], U]) -> Err[E]:
    """This `Err`, unchanged (an `Ok` applies `function` to its value)."""
    self._looked = True
    return self

  def __eq__(self, other: object) -> bool:
    return isinstance(other, Err) and other._error == self._error  # pyright: ignore[reportUnknownMemberType]

  def __hash__(self) -> int:
    return hash(("Err", repr(self._error)))

  def __repr__(self) -> str:
    return f"Err({self._error!r})"

  # Reporting an Err nobody looked at ----------------------------------------------

  def _describe(self) -> str:
    error = self._error
    where = " <- ".join(
      f"{name} ({file}:{line})" for file, line, name in self._made[:6]
    )
    return f"{type(error).__name__}: {error}   made at: {where}"

  def __del__(self) -> None:
    if self._looked or self._reported:
      return
    self._reported = True
    try:
      log.error(
        "An error result was dropped without being looked at: %s",
        self._describe(),
      )
    except Exception:  # noqa: S110  # at interpreter shutdown logging may already be gone
      pass


def _stack() -> tuple[_Frame, ...]:
  """The calling code's stack as light tuples, innermost first, skipping this module."""
  frames: list[_Frame] = []
  frame = sys._getframe(2)  # pyright: ignore[reportPrivateUsage]
  while frame is not None:
    code = frame.f_code
    if not code.co_filename.endswith(("/micro/result.py", "/micro/discord/_api.py")):
      frames.append((code.co_filename, frame.f_lineno, code.co_name))
    frame = frame.f_back  # pyright: ignore[reportAssignmentType]
  return tuple(frames)


type Result[T, E: Exception = Exception] = Ok[T] | Err[E]
"""Either an `Ok` with the value or an `Err` with the error."""


@contextmanager
def handling() -> Iterator[None]:
  """Watch the results made while this block runs (and by tasks it starts).

  When the block finishes normally and an `Err` made in it was never looked at,
  `UnhandledResult` is raised. If the block raises, that error stands and nothing is added.
  """
  scope: list[Err[Exception]] = []
  token = _scope.set(scope)
  try:
    yield
  except BaseException:
    for item in scope:
      item._reported = True  # pyright: ignore[reportPrivateUsage]
    raise
  finally:
    _scope.reset(token)
  unhandled = [item for item in scope if not item._looked]  # pyright: ignore[reportPrivateUsage]
  if unhandled:
    for item in unhandled:
      item._reported = True  # pyright: ignore[reportPrivateUsage]
    raise UnhandledResult(unhandled)


__all__ = ("Err", "Ok", "Result", "UnhandledResult", "handling")
