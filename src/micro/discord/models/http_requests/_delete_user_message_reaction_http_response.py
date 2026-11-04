# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._delete_user_message_reaction_http_response_body import DeleteUserMessageReactionHTTPResponseBody


class DeleteUserMessageReactionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteUserMessageReactionHTTPResponseBody | None = None
  raw_body: bytes
