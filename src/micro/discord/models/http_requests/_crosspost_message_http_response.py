# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._crosspost_message_http_response_body import CrosspostMessageHTTPResponseBody


class CrosspostMessageHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CrosspostMessageHTTPResponseBody | None = None
    raw_body: bytes
