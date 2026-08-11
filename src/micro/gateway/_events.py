from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


@dataclass(frozen=True, slots=True)
class Dispatch:
  name: str
  payload: Mapping[str, Any]
  shard_id: int = 0
  connection_id: str | None = None


class ConnectionEventKind(StrEnum):
  CONNECTED = "connected"
  DISCONNECTED = "disconnected"
  READY = "ready"
  RESUMED = "resumed"
  INVALIDATED = "invalidated"
  CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ConnectionEvent:
  kind: ConnectionEventKind
  shard_id: int
  connection_id: str | None = None


type DispatchSink = Callable[[Dispatch], Awaitable[None]]
type ConnectionSink = Callable[[ConnectionEvent], Awaitable[None]]
