# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_guild_http_response_body import UpdateGuildHTTPResponseBody


class UpdateGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildHTTPResponseBody | None = None
  raw_body: bytes
