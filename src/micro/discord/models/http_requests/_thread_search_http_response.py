# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._thread_search_http_response_body import ThreadSearchHTTPResponseBody


class ThreadSearchHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ThreadSearchHTTPResponseBody | None = None
    raw_body: bytes
