# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_webhook_http_response_body import UpdateWebhookHTTPResponseBody


class UpdateWebhookHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateWebhookHTTPResponseBody | None = None
    raw_body: bytes
