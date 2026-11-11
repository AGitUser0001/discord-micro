# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._add_lobby_member_http_response_body import AddLobbyMemberHTTPResponseBody


class AddLobbyMemberHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: AddLobbyMemberHTTPResponseBody | None = None
    raw_body: bytes
