# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_openid_connect_userinfo_http_response_body import GetOpenidConnectUserinfoHTTPResponseBody


class GetOpenidConnectUserinfoHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetOpenidConnectUserinfoHTTPResponseBody | None = None
    raw_body: bytes
