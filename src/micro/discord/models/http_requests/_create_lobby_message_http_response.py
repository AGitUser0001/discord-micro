# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_lobby_message_http_response_body import CreateLobbyMessageHTTPResponseBody


class CreateLobbyMessageHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateLobbyMessageHTTPResponseBody | None = None
    raw_body: bytes
