# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_my_guilds_http_response_body import ListMyGuildsHTTPResponseBody


class ListMyGuildsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListMyGuildsHTTPResponseBody | None = None
    raw_body: bytes
