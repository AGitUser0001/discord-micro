# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_webhook_message_http_response_body import GetWebhookMessageHTTPResponseBody


class GetWebhookMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetWebhookMessageHTTPResponseBody | None = None
  raw_body: bytes
