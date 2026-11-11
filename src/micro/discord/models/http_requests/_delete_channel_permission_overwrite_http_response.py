# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_channel_permission_overwrite_http_response_body import DeleteChannelPermissionOverwriteHTTPResponseBody


class DeleteChannelPermissionOverwriteHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteChannelPermissionOverwriteHTTPResponseBody | None = None
    raw_body: bytes
