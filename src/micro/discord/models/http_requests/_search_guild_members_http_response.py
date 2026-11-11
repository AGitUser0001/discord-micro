# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._search_guild_members_http_response_body import SearchGuildMembersHTTPResponseBody


class SearchGuildMembersHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: SearchGuildMembersHTTPResponseBody | None = None
    raw_body: bytes
