# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_original_webhook_message_http_response_body import UpdateOriginalWebhookMessageHTTPResponseBody


class UpdateOriginalWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateOriginalWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes
