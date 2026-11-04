# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_template_http_response_body import GetGuildTemplateHTTPResponseBody


class GetGuildTemplateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildTemplateHTTPResponseBody | None = None
  raw_body: bytes
