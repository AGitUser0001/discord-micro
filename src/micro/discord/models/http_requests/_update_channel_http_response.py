# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_channel_http_response_body import UpdateChannelHTTPResponseBody


class UpdateChannelHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateChannelHTTPResponseBody | None = None
    raw_body: bytes
