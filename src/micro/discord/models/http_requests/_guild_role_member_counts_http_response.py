# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._guild_role_member_counts_http_response_body import GuildRoleMemberCountsHTTPResponseBody


class GuildRoleMemberCountsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GuildRoleMemberCountsHTTPResponseBody | None = None
  raw_body: bytes
