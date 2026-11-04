# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._delete_guild_sticker_http_response_body import DeleteGuildStickerHTTPResponseBody


class DeleteGuildStickerHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteGuildStickerHTTPResponseBody | None = None
  raw_body: bytes
