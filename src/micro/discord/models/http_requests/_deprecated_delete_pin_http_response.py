# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._deprecated_delete_pin_http_response_body import DeprecatedDeletePinHTTPResponseBody


class DeprecatedDeletePinHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeprecatedDeletePinHTTPResponseBody | None = None
    raw_body: bytes
