# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_auto_moderation_rule_http_response_body import UpdateAutoModerationRuleHTTPResponseBody


class UpdateAutoModerationRuleHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateAutoModerationRuleHTTPResponseBody | None = None
  raw_body: bytes
