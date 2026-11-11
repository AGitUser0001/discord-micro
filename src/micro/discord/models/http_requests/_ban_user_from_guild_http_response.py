# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._ban_user_from_guild_http_response_body import BanUserFromGuildHTTPResponseBody


class BanUserFromGuildHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: BanUserFromGuildHTTPResponseBody | None = None
    raw_body: bytes
