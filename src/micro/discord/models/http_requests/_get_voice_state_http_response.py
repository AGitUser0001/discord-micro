# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_voice_state_http_response_body import GetVoiceStateHTTPResponseBody


class GetVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetVoiceStateHTTPResponseBody | None = None
  raw_body: bytes
