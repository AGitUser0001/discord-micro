from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

CONNECTION_HEADER = "Micro-Connection"
SHARD_HEADER = "Micro-Shard"
GENERATION_HEADER = "Micro-Generation"


class ConnectionEventKind(StrEnum):
  CONNECTED = "connected"
  DISCONNECTED = "disconnected"
  READY = "ready"
  RESUMED = "resumed"
  INVALIDATED = "invalidated"
  CLOSED = "closed"


class ConnectionEvent(BaseModel):
  """A Gateway connection lifecycle transition, published for the projection."""

  model_config = ConfigDict(extra="forbid", frozen=True)

  kind: ConnectionEventKind
  shard_id: int = Field(ge=0)
  generation: int = Field(ge=1)
  connection_id: str | None = None
  worker: str
