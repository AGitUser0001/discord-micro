"""Every event, work and periodic handler is called the same way: `(ctx)` for a periodic,
startup or shutdown handler, `(ctx, payload)` for the rest. Discord objects arrive bound to
the context (`micro.discord._bindings`)."""

import json
from collections.abc import Callable
from typing import Any

from micro import subjects

NO_PAYLOAD: Any = object()
"""Pass as the payload to call a handler that takes only the context."""


async def call_handler(
  service: Any,
  handler: Callable[..., Any],
  payload: Any = NO_PAYLOAD,
  message: Any = None,
) -> Any:
  """Call a handler with the service's `Context` and, if there is one, its payload."""
  from micro.discord._bindings import bound, context_of

  context = context_of(service)
  if payload is NO_PAYLOAD:
    return await handler(context)
  raw = (getattr(message, "headers", None) or {}).get(subjects.BEFORE_HEADER)
  return await handler(
    context, bound(payload, context, json.loads(raw) if raw else None)
  )
