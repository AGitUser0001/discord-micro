# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_original_webhook_message_http_response_body import GetOriginalWebhookMessageHTTPResponseBody


class GetOriginalWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetOriginalWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes
