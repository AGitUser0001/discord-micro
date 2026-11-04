# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_webhooks_http_response_body import GetGuildWebhooksHTTPResponseBody


class GetGuildWebhooksHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildWebhooksHTTPResponseBody | None = None
  raw_body: bytes
