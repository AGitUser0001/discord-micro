# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._send_soundboard_sound_http_response_body import SendSoundboardSoundHTTPResponseBody


class SendSoundboardSoundHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: SendSoundboardSoundHTTPResponseBody | None = None
    raw_body: bytes
