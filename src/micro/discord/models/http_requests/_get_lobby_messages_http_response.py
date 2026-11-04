# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_lobby_messages_http_response_body import GetLobbyMessagesHTTPResponseBody


class GetLobbyMessagesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetLobbyMessagesHTTPResponseBody | None = None
  raw_body: bytes
