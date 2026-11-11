# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_webhook_by_token_http_response_body import GetWebhookByTokenHTTPResponseBody


class GetWebhookByTokenHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetWebhookByTokenHTTPResponseBody | None = None
    raw_body: bytes
