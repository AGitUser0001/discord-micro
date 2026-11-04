# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_application_emoji_http_response_body import UpdateApplicationEmojiHTTPResponseBody


class UpdateApplicationEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateApplicationEmojiHTTPResponseBody | None = None
  raw_body: bytes
