# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_lobby_message_external_moderation_metadata_http_response_body import UpdateLobbyMessageExternalModerationMetadataHTTPResponseBody


class UpdateLobbyMessageExternalModerationMetadataHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateLobbyMessageExternalModerationMetadataHTTPResponseBody | None = None
    raw_body: bytes
