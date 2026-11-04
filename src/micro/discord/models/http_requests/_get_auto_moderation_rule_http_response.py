# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_auto_moderation_rule_http_response_body import GetAutoModerationRuleHTTPResponseBody


class GetAutoModerationRuleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetAutoModerationRuleHTTPResponseBody | None = None
  raw_body: bytes
