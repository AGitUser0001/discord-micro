# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._bulk_ban_users_from_guild_http_response_body import BulkBanUsersFromGuildHTTPResponseBody


class BulkBanUsersFromGuildHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: BulkBanUsersFromGuildHTTPResponseBody | None = None
    raw_body: bytes
