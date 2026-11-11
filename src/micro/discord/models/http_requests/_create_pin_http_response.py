# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_pin_http_response_body import CreatePinHTTPResponseBody


class CreatePinHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreatePinHTTPResponseBody | None = None
    raw_body: bytes
