# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_preview_http_response_body import GetGuildPreviewHTTPResponseBody


class GetGuildPreviewHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildPreviewHTTPResponseBody | None = None
  raw_body: bytes
