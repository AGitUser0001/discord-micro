# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_application_emoji_http_response_body import DeleteApplicationEmojiHTTPResponseBody


class DeleteApplicationEmojiHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteApplicationEmojiHTTPResponseBody | None = None
    raw_body: bytes
