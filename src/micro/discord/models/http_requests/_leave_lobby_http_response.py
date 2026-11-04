# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._leave_lobby_http_response_body import LeaveLobbyHTTPResponseBody


class LeaveLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: LeaveLobbyHTTPResponseBody | None = None
  raw_body: bytes
