# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._edit_lobby_http_response_body import EditLobbyHTTPResponseBody


class EditLobbyHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: EditLobbyHTTPResponseBody | None = None
  raw_body: bytes
