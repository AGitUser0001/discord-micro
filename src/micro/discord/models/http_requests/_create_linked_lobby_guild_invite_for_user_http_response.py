# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._create_linked_lobby_guild_invite_for_user_http_response_body import CreateLinkedLobbyGuildInviteForUserHTTPResponseBody


class CreateLinkedLobbyGuildInviteForUserHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateLinkedLobbyGuildInviteForUserHTTPResponseBody | None = None
  raw_body: bytes
