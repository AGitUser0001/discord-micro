# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._action_guild_join_request_http_response_body import ActionGuildJoinRequestHTTPResponseBody


class ActionGuildJoinRequestHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ActionGuildJoinRequestHTTPResponseBody | None = None
  raw_body: bytes
