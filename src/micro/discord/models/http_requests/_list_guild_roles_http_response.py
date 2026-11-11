# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_guild_roles_http_response_body import ListGuildRolesHTTPResponseBody


class ListGuildRolesHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListGuildRolesHTTPResponseBody | None = None
    raw_body: bytes
