# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._execute_slack_compatible_webhook_http_response_body import ExecuteSlackCompatibleWebhookHTTPResponseBody


class ExecuteSlackCompatibleWebhookHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ExecuteSlackCompatibleWebhookHTTPResponseBody | None = None
  raw_body: bytes
