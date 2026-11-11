# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_guild_scheduled_event_http_response_body import UpdateGuildScheduledEventHTTPResponseBody


class UpdateGuildScheduledEventHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateGuildScheduledEventHTTPResponseBody | None = None
    raw_body: bytes
