# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_guild_stickers_http_response_body import ListGuildStickersHTTPResponseBody


class ListGuildStickersHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListGuildStickersHTTPResponseBody | None = None
    raw_body: bytes
