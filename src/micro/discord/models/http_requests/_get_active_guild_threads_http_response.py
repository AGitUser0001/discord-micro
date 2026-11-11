# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_active_guild_threads_http_response_body import GetActiveGuildThreadsHTTPResponseBody


class GetActiveGuildThreadsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetActiveGuildThreadsHTTPResponseBody | None = None
    raw_body: bytes
