# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._set_channel_permission_overwrite_http_response_body import SetChannelPermissionOverwriteHTTPResponseBody


class SetChannelPermissionOverwriteHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: SetChannelPermissionOverwriteHTTPResponseBody | None = None
    raw_body: bytes
