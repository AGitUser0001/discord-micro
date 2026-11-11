# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_guild_member_role_http_response_body import DeleteGuildMemberRoleHTTPResponseBody


class DeleteGuildMemberRoleHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteGuildMemberRoleHTTPResponseBody | None = None
    raw_body: bytes
