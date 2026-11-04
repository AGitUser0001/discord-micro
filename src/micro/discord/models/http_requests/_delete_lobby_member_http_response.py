# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._delete_lobby_member_http_response_body import DeleteLobbyMemberHTTPResponseBody


class DeleteLobbyMemberHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeleteLobbyMemberHTTPResponseBody | None = None
  raw_body: bytes
