# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_application_user_role_connection_http_response_body import GetApplicationUserRoleConnectionHTTPResponseBody


class GetApplicationUserRoleConnectionHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetApplicationUserRoleConnectionHTTPResponseBody | None = None
    raw_body: bytes
