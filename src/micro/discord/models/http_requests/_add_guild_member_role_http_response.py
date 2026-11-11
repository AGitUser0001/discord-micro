# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._add_guild_member_role_http_response_body import AddGuildMemberRoleHTTPResponseBody


class AddGuildMemberRoleHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: AddGuildMemberRoleHTTPResponseBody | None = None
    raw_body: bytes
