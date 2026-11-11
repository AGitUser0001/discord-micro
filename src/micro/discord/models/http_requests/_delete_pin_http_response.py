# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_pin_http_response_body import DeletePinHTTPResponseBody


class DeletePinHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeletePinHTTPResponseBody | None = None
    raw_body: bytes
