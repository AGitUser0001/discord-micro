"""Builtin schemas, imported on first use: `micro.schemas.events` (one per Discord dispatch)."""

from typing import TYPE_CHECKING

from micro._lazy import exports

if TYPE_CHECKING:
  from . import events as events
else:
  __getattr__, __dir__ = exports(__name__, {"events": ".events"})

__all__ = ("events",)
