# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_guild_soundboard_sound_http_response_body import DeleteGuildSoundboardSoundHTTPResponseBody


class DeleteGuildSoundboardSoundHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteGuildSoundboardSoundHTTPResponseBody | None = None
    raw_body: bytes
