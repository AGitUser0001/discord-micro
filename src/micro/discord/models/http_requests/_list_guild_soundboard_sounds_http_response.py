# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_guild_soundboard_sounds_http_response_body import ListGuildSoundboardSoundsHTTPResponseBody


class ListGuildSoundboardSoundsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListGuildSoundboardSoundsHTTPResponseBody | None = None
    raw_body: bytes
