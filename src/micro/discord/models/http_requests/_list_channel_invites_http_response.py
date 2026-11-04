# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_channel_invites_http_response_body import ListChannelInvitesHTTPResponseBody


class ListChannelInvitesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListChannelInvitesHTTPResponseBody | None = None
  raw_body: bytes
