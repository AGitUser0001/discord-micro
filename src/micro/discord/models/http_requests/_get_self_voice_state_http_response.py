# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_self_voice_state_http_response_body import GetSelfVoiceStateHTTPResponseBody


class GetSelfVoiceStateHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetSelfVoiceStateHTTPResponseBody | None = None
  raw_body: bytes
