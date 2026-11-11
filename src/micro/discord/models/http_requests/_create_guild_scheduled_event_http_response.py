# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_guild_scheduled_event_http_response_body import CreateGuildScheduledEventHTTPResponseBody


class CreateGuildScheduledEventHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateGuildScheduledEventHTTPResponseBody | None = None
    raw_body: bytes
