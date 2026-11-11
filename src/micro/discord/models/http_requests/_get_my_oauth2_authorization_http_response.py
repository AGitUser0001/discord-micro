# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_my_oauth2_authorization_http_response_body import GetMyOauth2AuthorizationHTTPResponseBody


class GetMyOauth2AuthorizationHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetMyOauth2AuthorizationHTTPResponseBody | None = None
    raw_body: bytes
