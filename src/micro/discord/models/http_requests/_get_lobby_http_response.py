# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_lobby_http_response_body import GetLobbyHTTPResponseBody


class GetLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetLobbyHTTPResponseBody | None = None
  raw_body: bytes
