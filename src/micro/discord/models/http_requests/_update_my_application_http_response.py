# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_my_application_http_response_body import UpdateMyApplicationHTTPResponseBody


class UpdateMyApplicationHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateMyApplicationHTTPResponseBody | None = None
    raw_body: bytes
