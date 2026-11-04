# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_voice_channel_status_http_response_body import UpdateVoiceChannelStatusHTTPResponseBody


class UpdateVoiceChannelStatusHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateVoiceChannelStatusHTTPResponseBody | None = None
  raw_body: bytes
