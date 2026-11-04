# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._create_channel_invite_http_response_body import CreateChannelInviteHTTPResponseBody


class CreateChannelInviteHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateChannelInviteHTTPResponseBody | None = None
  raw_body: bytes
