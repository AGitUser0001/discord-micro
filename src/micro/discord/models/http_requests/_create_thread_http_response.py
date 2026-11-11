# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_thread_http_response_body import CreateThreadHTTPResponseBody


class CreateThreadHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateThreadHTTPResponseBody | None = None
    raw_body: bytes
