# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_sticker_packs_http_response_body import ListStickerPacksHTTPResponseBody


class ListStickerPacksHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListStickerPacksHTTPResponseBody | None = None
  raw_body: bytes
