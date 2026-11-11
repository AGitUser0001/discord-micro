# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_or_join_lobby_http_response_body import CreateOrJoinLobbyHTTPResponseBody


class CreateOrJoinLobbyHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateOrJoinLobbyHTTPResponseBody | None = None
    raw_body: bytes
