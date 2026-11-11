# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._edit_lobby_channel_link_http_response_body import EditLobbyChannelLinkHTTPResponseBody


class EditLobbyChannelLinkHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: EditLobbyChannelLinkHTTPResponseBody | None = None
    raw_body: bytes
