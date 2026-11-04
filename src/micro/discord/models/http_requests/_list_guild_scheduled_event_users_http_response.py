# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_guild_scheduled_event_users_http_response_body import ListGuildScheduledEventUsersHTTPResponseBody


class ListGuildScheduledEventUsersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildScheduledEventUsersHTTPResponseBody | None = None
  raw_body: bytes
