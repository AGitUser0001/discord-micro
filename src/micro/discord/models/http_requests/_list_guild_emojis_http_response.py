# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_guild_emojis_http_response_body import ListGuildEmojisHTTPResponseBody


class ListGuildEmojisHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListGuildEmojisHTTPResponseBody | None = None
    raw_body: bytes
