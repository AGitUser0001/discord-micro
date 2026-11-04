# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._delete_webhook_message_http_response_body import DeleteWebhookMessageHTTPResponseBody


class DeleteWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes
