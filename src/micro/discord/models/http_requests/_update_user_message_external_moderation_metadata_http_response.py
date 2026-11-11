# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_user_message_external_moderation_metadata_http_response_body import UpdateUserMessageExternalModerationMetadataHTTPResponseBody


class UpdateUserMessageExternalModerationMetadataHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateUserMessageExternalModerationMetadataHTTPResponseBody | None = None
    raw_body: bytes
