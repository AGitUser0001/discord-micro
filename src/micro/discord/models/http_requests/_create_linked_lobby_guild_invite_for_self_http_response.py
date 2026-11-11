# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_linked_lobby_guild_invite_for_self_http_response_body import CreateLinkedLobbyGuildInviteForSelfHTTPResponseBody


class CreateLinkedLobbyGuildInviteForSelfHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateLinkedLobbyGuildInviteForSelfHTTPResponseBody | None = None
    raw_body: bytes
