# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._create_guild_soundboard_sound_http_response_body import CreateGuildSoundboardSoundHTTPResponseBody


class CreateGuildSoundboardSoundHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateGuildSoundboardSoundHTTPResponseBody | None = None
  raw_body: bytes
