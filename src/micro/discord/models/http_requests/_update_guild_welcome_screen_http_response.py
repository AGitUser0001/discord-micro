# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_guild_welcome_screen_http_response_body import UpdateGuildWelcomeScreenHTTPResponseBody


class UpdateGuildWelcomeScreenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildWelcomeScreenHTTPResponseBody | None = None
  raw_body: bytes
