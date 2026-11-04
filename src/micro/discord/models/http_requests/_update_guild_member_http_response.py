# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_guild_member_http_response_body import UpdateGuildMemberHTTPResponseBody


class UpdateGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildMemberHTTPResponseBody | None = None
  raw_body: bytes
