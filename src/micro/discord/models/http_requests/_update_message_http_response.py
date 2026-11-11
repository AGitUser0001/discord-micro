# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_message_http_response_body import UpdateMessageHTTPResponseBody


class UpdateMessageHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateMessageHTTPResponseBody | None = None
    raw_body: bytes
