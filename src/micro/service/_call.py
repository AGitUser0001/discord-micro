"""What a Service middleware sees: one request, event or job on its way to a handler."""

from typing import TYPE_CHECKING, Any, Literal

from nats.aio.msg import Msg

if TYPE_CHECKING:
  from ._service import Service


class _Unset:
  def __repr__(self) -> str:
    return "UNSET"


UNSET: Any = _Unset()


class Call:
  """One delivery on its way to a handler.

  * `kind`: `"request"`, `"event"` or `"work"`; `key` is the request ID, event ID
    or queue name that `use("scope", fn)` matches.
  * `input` is the decoded request, event or job; replace it before `next()` to
    change what the handler gets.
  * `output` is a request's reply, set once the handler ran. A middleware that
    calls `end()` without calling `next()` must set it itself, or the caller gets
    an `ended_without_reply` error. Events and jobs have no output; `end()` there
    counts as handled.
  * `state` is scratch space for middleware to share; `reached` says whether the
    call got all the way to the handler.
  """

  __slots__ = (
    "input",
    "key",
    "kind",
    "message",
    "output",
    "reached",
    "service",
    "state",
  )

  def __init__(
    self,
    kind: Literal["request", "event", "work"],
    key: str,
    service: Service,
    message: Msg,
    input: Any,
  ) -> None:
    self.kind = kind
    self.key = key
    self.service = service
    self.message = message
    self.input = input
    self.output: Any = UNSET
    self.state: dict[str, Any] = {}
    self.reached = False
