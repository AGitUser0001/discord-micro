# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_lobby_http_response_body import CreateLobbyHTTPResponseBody


class CreateLobbyHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateLobbyHTTPResponseBody | None = None
    raw_body: bytes
