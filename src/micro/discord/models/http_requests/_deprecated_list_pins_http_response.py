# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._deprecated_list_pins_http_response_body import DeprecatedListPinsHTTPResponseBody


class DeprecatedListPinsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeprecatedListPinsHTTPResponseBody | None = None
    raw_body: bytes
