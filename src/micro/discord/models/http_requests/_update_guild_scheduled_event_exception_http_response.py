# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_guild_scheduled_event_exception_http_response_body import UpdateGuildScheduledEventExceptionHTTPResponseBody


class UpdateGuildScheduledEventExceptionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildScheduledEventExceptionHTTPResponseBody | None = None
  raw_body: bytes
