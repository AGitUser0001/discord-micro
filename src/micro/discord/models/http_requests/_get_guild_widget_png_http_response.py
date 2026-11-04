# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_widget_png_http_response_body import GetGuildWidgetPngHTTPResponseBody


class GetGuildWidgetPngHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWidgetPngHTTPResponseBody | None = None
  raw_body: bytes
