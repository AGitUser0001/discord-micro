# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_guild_scheduled_event_exception_http_response_body import DeleteGuildScheduledEventExceptionHTTPResponseBody


class DeleteGuildScheduledEventExceptionHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteGuildScheduledEventExceptionHTTPResponseBody | None = None
    raw_body: bytes
