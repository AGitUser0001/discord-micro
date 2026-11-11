# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_voice_regions_http_response_body import ListVoiceRegionsHTTPResponseBody


class ListVoiceRegionsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListVoiceRegionsHTTPResponseBody | None = None
    raw_body: bytes
