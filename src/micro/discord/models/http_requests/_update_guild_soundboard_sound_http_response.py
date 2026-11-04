# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_guild_soundboard_sound_http_response_body import UpdateGuildSoundboardSoundHTTPResponseBody


class UpdateGuildSoundboardSoundHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateGuildSoundboardSoundHTTPResponseBody | None = None
  raw_body: bytes
