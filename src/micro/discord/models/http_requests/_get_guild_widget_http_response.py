# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_widget_http_response_body import GetGuildWidgetHTTPResponseBody


class GetGuildWidgetHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWidgetHTTPResponseBody | None = None
  raw_body: bytes
