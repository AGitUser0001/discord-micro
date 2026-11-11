# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._bulk_update_lobby_members_http_response_body import BulkUpdateLobbyMembersHTTPResponseBody


class BulkUpdateLobbyMembersHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: BulkUpdateLobbyMembersHTTPResponseBody | None = None
    raw_body: bytes
