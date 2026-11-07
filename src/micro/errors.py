"""The stable exception hierarchy shared by every Micro package."""

from typing import Any

from pydantic import JsonValue


class MicroError(Exception):
  """Base exception for expected Micro framework failures."""


class RoutingError(MicroError, LookupError):
  """No live component can receive a request."""


class TopologyError(MicroError, ValueError):
  """Declared components or ownership conflict with each other."""


class BackendExecutionError(MicroError, RuntimeError):
  """A storage or external backend failed to execute an operation."""


class RequestTimeoutError(MicroError, TimeoutError):
  """A request received no reply in time."""


class DrainingError(MicroError, RuntimeError):
  """A component refused new work because it is draining or closed."""


class ServiceError(MicroError):
  """An application error a handler deliberately returns to its caller.

  Raise it inside a request handler; the caller receives a `RemoteError` carrying
  the same `code`, `message`, and `detail`.
  """

  def __init__(
    self, code: str, message: str, *, detail: JsonValue | None = None
  ) -> None:
    if not code:
      raise ValueError("Service error codes cannot be empty.")
    self.code = code
    self.message = message
    self.detail = detail
    super().__init__(f"{code}: {message}")

  def document(self) -> dict[str, Any]:
    """The error as `{code, message, detail}`, as sent to the caller."""
    return {"code": self.code, "message": self.message, "detail": self.detail}


class RemoteError(MicroError, RuntimeError):
  """A remote component answered a request with an error.

  Framework codes are `invalid_input`, `invalid_output`, `incompatible_schema`,
  `handler_failed`, and `draining`; any other code came from a `ServiceError`.
  """

  def __init__(
    self,
    target: str,
    code: str,
    message: str,
    *,
    detail: JsonValue | None = None,
  ) -> None:
    self.target = target
    self.code = code
    self.message = message
    self.detail = detail
    super().__init__(f"{target} failed with {code}: {message}")


__all__ = (
  "BackendExecutionError",
  "DrainingError",
  "MicroError",
  "RemoteError",
  "RequestTimeoutError",
  "RoutingError",
  "ServiceError",
  "TopologyError",
)
