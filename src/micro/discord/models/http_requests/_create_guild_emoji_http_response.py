# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._create_guild_emoji_http_response_body import CreateGuildEmojiHTTPResponseBody


class CreateGuildEmojiHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildEmojiHTTPResponseBody | None = None
  raw_body: bytes
