# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_message_reactions_by_emoji_http_response_body import ListMessageReactionsByEmojiHTTPResponseBody


class ListMessageReactionsByEmojiHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListMessageReactionsByEmojiHTTPResponseBody | None = None
    raw_body: bytes
