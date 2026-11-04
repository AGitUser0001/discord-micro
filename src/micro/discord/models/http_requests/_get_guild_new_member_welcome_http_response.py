# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_guild_new_member_welcome_http_response_body import GetGuildNewMemberWelcomeHTTPResponseBody


class GetGuildNewMemberWelcomeHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetGuildNewMemberWelcomeHTTPResponseBody | None = None
  raw_body: bytes
