# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_my_application_http_response_body import GetMyApplicationHTTPResponseBody


class GetMyApplicationHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetMyApplicationHTTPResponseBody | None = None
    raw_body: bytes
