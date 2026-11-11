# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._count_guild_scheduled_event_users_http_response_body import CountGuildScheduledEventUsersHTTPResponseBody


class CountGuildScheduledEventUsersHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CountGuildScheduledEventUsersHTTPResponseBody | None = None
    raw_body: bytes
