# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_bot_gateway_http_response_body import GetBotGatewayHTTPResponseBody


class GetBotGatewayHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetBotGatewayHTTPResponseBody | None = None
    raw_body: bytes
