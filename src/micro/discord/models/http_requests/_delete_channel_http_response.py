# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._delete_channel_http_response_body import DeleteChannelHTTPResponseBody


class DeleteChannelHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteChannelHTTPResponseBody | None = None
  raw_body: bytes
