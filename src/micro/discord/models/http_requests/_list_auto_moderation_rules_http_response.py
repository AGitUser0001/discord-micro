# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_auto_moderation_rules_http_response_body import ListAutoModerationRulesHTTPResponseBody


class ListAutoModerationRulesHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListAutoModerationRulesHTTPResponseBody | None = None
    raw_body: bytes
