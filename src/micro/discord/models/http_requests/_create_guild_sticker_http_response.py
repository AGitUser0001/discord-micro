# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_guild_sticker_http_response_body import CreateGuildStickerHTTPResponseBody


class CreateGuildStickerHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateGuildStickerHTTPResponseBody | None = None
    raw_body: bytes
