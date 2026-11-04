# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_webhook_message_http_response_body import UpdateWebhookMessageHTTPResponseBody


class UpdateWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes
