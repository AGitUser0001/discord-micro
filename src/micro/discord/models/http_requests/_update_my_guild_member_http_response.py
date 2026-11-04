# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_my_guild_member_http_response_body import UpdateMyGuildMemberHTTPResponseBody


class UpdateMyGuildMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateMyGuildMemberHTTPResponseBody | None = None
  raw_body: bytes
