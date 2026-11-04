# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_sticker_http_response_body import GetGuildStickerHTTPResponseBody


class GetGuildStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildStickerHTTPResponseBody | None = None
  raw_body: bytes
