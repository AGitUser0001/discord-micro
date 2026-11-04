# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._follow_channel_http_response_body import FollowChannelHTTPResponseBody


class FollowChannelHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: FollowChannelHTTPResponseBody | None = None
  raw_body: bytes
