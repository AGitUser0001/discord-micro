# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_guild_templates_http_response_body import ListGuildTemplatesHTTPResponseBody


class ListGuildTemplatesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildTemplatesHTTPResponseBody | None = None
  raw_body: bytes
