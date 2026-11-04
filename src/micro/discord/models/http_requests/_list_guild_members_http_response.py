# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_guild_members_http_response_body import ListGuildMembersHTTPResponseBody


class ListGuildMembersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildMembersHTTPResponseBody | None = None
  raw_body: bytes
