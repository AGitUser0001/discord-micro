# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_guild_scheduled_event_http_response_body import GetGuildScheduledEventHTTPResponseBody


class GetGuildScheduledEventHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetGuildScheduledEventHTTPResponseBody | None = None
    raw_body: bytes
