# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._guild_search_http_response_body import GuildSearchHTTPResponseBody


class GuildSearchHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GuildSearchHTTPResponseBody | None = None
  raw_body: bytes
