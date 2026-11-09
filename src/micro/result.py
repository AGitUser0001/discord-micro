"""Results: a call that can fail in an expected way returns its outcome as a value.

    match await message.edit(content="hi"):
      case Ok(edited): ...
      case Err(NotFound()): ...            # it was deleted meanwhile
      case Err(error): raise error

    text = (await channel.send("hi")).unwrap()         # abort: the error is raised
    sent = (await channel.send("hi")).ok()              # the message, or None
    await (await message.delete()).ignore(NotFound)     # only "already gone" is fine

A `Result[T, E]` is an `Ok` holding the `T` or an `Err` holding the `E`. Handle it where
you need to (`match`, `ok()`, `unwrap_or(default)`) or pass it on as a failure with
`unwrap()`, which raises the original error so the generic handler sees it unchanged.
Failures that are bugs or broken infrastructure (a bad argument, NATS down) are not
results: they raise, as ever.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, NoReturn


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


@dataclass(frozen=True, slots=True)
class Err[E: Exception]:
  """The call failed in an expected way; `error` says how."""

  error: E

  @property
  def is_ok(self) -> Literal[False]:
    """False: the call failed."""
    return False

  @property
  def is_err(self) -> Literal[True]:
    """True: the call failed."""
    return True

  def ok(self) -> None:
    """None, as there is no value (an `Ok` gives its value here)."""
    return

  def unwrap(self) -> NoReturn:
    """Raise the error (an `Ok` gives its value here)."""
    raise self.error

  def unwrap_or[D](self, default: D) -> D:
    """`default`, as there is no value (an `Ok` gives its value here)."""
    return default

  def ignore(self, *errors: type[Exception]) -> None:
    """None if the error is one of `errors`; any other error is raised."""
    if isinstance(self.error, errors):
      return
    raise self.error

  def map[U](self, function: Callable[[object], U]) -> Err[E]:
    """This `Err`, unchanged (an `Ok` applies `function` to its value)."""
    return self


type Result[T, E: Exception = Exception] = Ok[T] | Err[E]
"""Either an `Ok` with the value or an `Err` with the error."""

__all__ = ("Err", "Ok", "Result")
