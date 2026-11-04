# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._delete_all_message_reactions_http_response_body import DeleteAllMessageReactionsHTTPResponseBody


class DeleteAllMessageReactionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteAllMessageReactionsHTTPResponseBody | None = None
  raw_body: bytes
