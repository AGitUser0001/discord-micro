# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_my_message_reaction_http_response_body import DeleteMyMessageReactionHTTPResponseBody


class DeleteMyMessageReactionHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteMyMessageReactionHTTPResponseBody | None = None
    raw_body: bytes
