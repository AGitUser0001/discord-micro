# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._execute_webhook_http_response_body import ExecuteWebhookHTTPResponseBody


class ExecuteWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ExecuteWebhookHTTPResponseBody | None = None
  raw_body: bytes
