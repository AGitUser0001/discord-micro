# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_application_http_response_body import GetApplicationHTTPResponseBody


class GetApplicationHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetApplicationHTTPResponseBody | None = None
    raw_body: bytes
