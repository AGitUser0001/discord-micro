# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_self_voice_state_http_response_body import UpdateSelfVoiceStateHTTPResponseBody


class UpdateSelfVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateSelfVoiceStateHTTPResponseBody | None = None
  raw_body: bytes
