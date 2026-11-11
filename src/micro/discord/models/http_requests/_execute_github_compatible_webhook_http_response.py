# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._execute_github_compatible_webhook_http_response_body import ExecuteGithubCompatibleWebhookHTTPResponseBody


class ExecuteGithubCompatibleWebhookHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ExecuteGithubCompatibleWebhookHTTPResponseBody | None = None
    raw_body: bytes
