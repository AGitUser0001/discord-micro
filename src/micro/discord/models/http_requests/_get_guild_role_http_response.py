# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_guild_role_http_response_body import GetGuildRoleHTTPResponseBody


class GetGuildRoleHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetGuildRoleHTTPResponseBody | None = None
    raw_body: bytes
