# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_voice_state_http_response_body import UpdateVoiceStateHTTPResponseBody


class UpdateVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateVoiceStateHTTPResponseBody | None = None
  raw_body: bytes
