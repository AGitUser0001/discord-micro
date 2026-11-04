# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_guild_bans_http_response_body import ListGuildBansHTTPResponseBody


class ListGuildBansHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildBansHTTPResponseBody | None = None
  raw_body: bytes
