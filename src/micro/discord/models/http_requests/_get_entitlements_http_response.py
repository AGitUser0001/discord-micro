# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_entitlements_http_response_body import GetEntitlementsHTTPResponseBody


class GetEntitlementsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetEntitlementsHTTPResponseBody | None = None
    raw_body: bytes
