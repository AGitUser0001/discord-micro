# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_auto_moderation_rule_http_response_body import DeleteAutoModerationRuleHTTPResponseBody


class DeleteAutoModerationRuleHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteAutoModerationRuleHTTPResponseBody | None = None
    raw_body: bytes
