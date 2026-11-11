# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_user_http_response_body import GetUserHTTPResponseBody


class GetUserHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetUserHTTPResponseBody | None = None
    raw_body: bytes
