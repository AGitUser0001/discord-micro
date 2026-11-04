# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._add_my_message_reaction_http_response_body import AddMyMessageReactionHTTPResponseBody


class AddMyMessageReactionHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: AddMyMessageReactionHTTPResponseBody | None = None
  raw_body: bytes
