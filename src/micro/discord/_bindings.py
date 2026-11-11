"""What event handlers can ask for by annotation (see `micro.service._inject`):
`ctx: Context`, and a payload as a bound `Message`, `Member`, `User`, `Channel`, `Guild`
or `Role`. Imported on first use by the service; nothing to call."""

from typing import Any
from weakref import WeakKeyDictionary

from pydantic import BaseModel

from micro.discord import objects
from micro.discord.interactions._application import Context
from micro.service._inject import convertible, injectable

_contexts: WeakKeyDictionary[Any, Context] = WeakKeyDictionary()


def context_of(service: Any) -> Context:
  """The `Context` of a service (one per service)."""
  context = _contexts.get(service)
  if context is None:
    from micro.discord.http_service import DiscordHTTPClient

    context = Context(DiscordHTTPClient(service.runtime), service=service)
    _contexts[service] = context
  return context


def _data(payload: Any) -> dict[str, Any]:
  if isinstance(payload, BaseModel):
    return payload.model_dump(mode="json", by_alias=True)
  return dict(payload)


injectable(Context, context_of)
for _view in (
  objects.Message,
  objects.Member,
  objects.User,
  objects.Channel,
  objects.Guild,
  objects.Role,
):
  convertible(
    _view,
    lambda payload, service, view=_view: view.model_validate(_data(payload)).bind(
      context_of(service)
    ),
  )
