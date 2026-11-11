# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._trigger_typing_indicator_http_response_body import TriggerTypingIndicatorHTTPResponseBody


class TriggerTypingIndicatorHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: TriggerTypingIndicatorHTTPResponseBody | None = None
    raw_body: bytes
