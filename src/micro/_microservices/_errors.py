class MicroError(Exception):
  """Base exception for expected Micro framework failures."""


class RoutingError(MicroError, LookupError):
  pass


class RemoteResponseError(MicroError, RuntimeError):
  pass


class TopologyError(MicroError, ValueError):
  pass


class QueueSettlementError(MicroError, RuntimeError):
  pass


class BackendExecutionError(MicroError, RuntimeError):
  pass


__all__ = (
  "BackendExecutionError",
  "MicroError",
  "QueueSettlementError",
  "RemoteResponseError",
  "RoutingError",
  "TopologyError",
)
