# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_guild_scheduled_events_http_response_body import ListGuildScheduledEventsHTTPResponseBody


class ListGuildScheduledEventsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildScheduledEventsHTTPResponseBody | None = None
  raw_body: bytes
