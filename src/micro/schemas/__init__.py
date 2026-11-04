"""Builtin schemas, imported on first use (`gateway` needs the store extra)."""

from typing import TYPE_CHECKING

from micro._lazy import exports

if TYPE_CHECKING:
  from . import events as events
  from . import gateway as gateway

__getattr__, __dir__ = exports(__name__, {"events": ".events", "gateway": ".gateway"})

__all__ = ("events", "gateway")
