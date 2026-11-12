"""How the service hands Discord objects to handlers (see `micro.service._inject`): the
service's `Context`, and payloads bound to it. Imported on first use; nothing to call."""

from typing import Any
from weakref import WeakKeyDictionary

from micro.discord import objects
from micro.discord.interactions._application import Context

_contexts: WeakKeyDictionary[Any, Context] = WeakKeyDictionary()


def context_of(service: Any) -> Context:
  """The `Context` of a service (one per service)."""
  context = _contexts.get(service)
  if context is None:
    from micro.discord.http_service import DiscordHTTPClient

    context = Context(DiscordHTTPClient(service.runtime), service=service)
    _contexts[service] = context
  return context


def bound(payload: Any, context: Context, before: Any = None) -> Any:
  """A payload that is a Discord object, bound to `context` (with `before`, the object as
  it was, when the event changed one); anything else as it is."""
  if not isinstance(payload, objects._View):
    return payload
  result = payload.bind(context)
  if before is not None:
    guild_id = getattr(payload, "guild_id", None)
    if isinstance(before, dict) and guild_id and "guild_id" not in before:
      before = {**before, "guild_id": guild_id}
    result._before = type(payload).model_validate(before).bind(context)
  return result
