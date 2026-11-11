# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_messages_http_response_body import ListMessagesHTTPResponseBody


class ListMessagesHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListMessagesHTTPResponseBody | None = None
    raw_body: bytes
