from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueBackendDelivery:
  """Queue-backend metadata that never enters an application's payload."""

  payload: bytes
  receipt: str
  reply: str | None = None
