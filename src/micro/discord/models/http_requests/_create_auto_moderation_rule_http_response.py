# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._create_auto_moderation_rule_http_response_body import CreateAutoModerationRuleHTTPResponseBody


class CreateAutoModerationRuleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateAutoModerationRuleHTTPResponseBody | None = None
  raw_body: bytes
