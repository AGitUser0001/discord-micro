# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_sticker_http_response_body import GetStickerHTTPResponseBody


class GetStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetStickerHTTPResponseBody | None = None
  raw_body: bytes
