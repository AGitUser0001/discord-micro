# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_channel_role_permissions_http_response_body import GetChannelRolePermissionsHTTPResponseBody


class GetChannelRolePermissionsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetChannelRolePermissionsHTTPResponseBody | None = None
    raw_body: bytes
