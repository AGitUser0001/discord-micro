from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueBackendDelivery:
  """Queue-backend metadata that never enters an application's payload."""

  payload: bytes
  receipt: str
  reply: str | None = None


@dataclass(frozen=True, slots=True)
class QueueObservation:
  connected: bool
  pending: int | None = None
  consumers: int | None = None
