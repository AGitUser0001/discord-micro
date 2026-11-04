# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_vanity_url_http_response_body import GetGuildVanityUrlHTTPResponseBody


class GetGuildVanityUrlHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildVanityUrlHTTPResponseBody | None = None
  raw_body: bytes
