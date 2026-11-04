# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._leave_guild_http_response_body import LeaveGuildHTTPResponseBody


class LeaveGuildHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: LeaveGuildHTTPResponseBody | None = None
  raw_body: bytes
