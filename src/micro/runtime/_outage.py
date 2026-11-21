"""When NATS goes away: one line when it starts, one when it is back.

Everything that talks to NATS keeps trying while it is away (presence renews, the Gateway
reconciles and publishes). Logging a traceback on every attempt buries the one thing worth
knowing, that NATS was unavailable and for how long, under hundreds of identical lines.
An `Outage` logs the first failure and the recovery; any other error is still the caller's
to log, with its traceback, because that one is a bug.
"""

from nats import errors as nats_errors
from nats.js import errors as jetstream_errors

from micro import log

UNAVAILABLE: tuple[type[BaseException], ...] = (
  nats_errors.TimeoutError,
  nats_errors.ConnectionClosedError,
  nats_errors.ConnectionReconnectingError,
  nats_errors.ConnectionDrainingError,
  nats_errors.StaleConnectionError,
  nats_errors.OutboundBufferLimitError,
  nats_errors.NoServersError,
  nats_errors.FlushTimeoutError,
  jetstream_errors.ServiceUnavailableError,
  ConnectionError,
)
"""Errors that mean NATS (or its JetStream) is not answering, not that the request is wrong."""


def unavailable(error: BaseException) -> bool:
  """Whether `error` means NATS is not answering right now."""
  return isinstance(error, UNAVAILABLE)


class Outage:
  """Counts failed attempts while NATS is away, and says so twice: at the start and at the
  end. `what` names the work ("Renewing presence x"); `counted` says what each failure
  cost ("attempt(s) failed", "event(s) were lost")."""

  def __init__(self, what: str, *, counted: str = "attempt(s) failed") -> None:
    self.what = what
    self.counted = counted
    self.failures = 0

  def failed(self, error: BaseException) -> bool:
    """Record a failure. True if it was NATS being unavailable (logged once per outage);
    False for any other error, which the caller should log as the bug it is."""
    if not unavailable(error):
      return False
    if self.failures == 0:
      log.warning(
        "%s: NATS is not answering (%s); retrying quietly until it does",
        self.what,
        str(error) or type(error).__name__,
      )
    self.failures += 1
    return True

  def recovered(self) -> None:
    """Record a success: if an outage was going on, say it is over and what it cost."""
    if self.failures:
      log.warning(
        "%s works again; %d %s while NATS was away",
        self.what,
        self.failures,
        self.counted,
      )
      self.failures = 0
