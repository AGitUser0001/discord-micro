# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._delete_webhook_by_token_http_response_body import DeleteWebhookByTokenHTTPResponseBody


class DeleteWebhookByTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteWebhookByTokenHTTPResponseBody | None = None
  raw_body: bytes
