# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_original_webhook_message_http_response_body import DeleteOriginalWebhookMessageHTTPResponseBody


class DeleteOriginalWebhookMessageHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteOriginalWebhookMessageHTTPResponseBody | None = None
    raw_body: bytes
