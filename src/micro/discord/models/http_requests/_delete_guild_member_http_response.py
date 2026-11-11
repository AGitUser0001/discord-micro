# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_guild_member_http_response_body import DeleteGuildMemberHTTPResponseBody


class DeleteGuildMemberHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteGuildMemberHTTPResponseBody | None = None
    raw_body: bytes
