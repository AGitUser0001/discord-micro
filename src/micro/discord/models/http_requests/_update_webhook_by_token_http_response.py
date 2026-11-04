# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_webhook_by_token_http_response_body import UpdateWebhookByTokenHTTPResponseBody


class UpdateWebhookByTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateWebhookByTokenHTTPResponseBody | None = None
  raw_body: bytes
