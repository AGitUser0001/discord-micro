# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_application_role_connections_metadata_http_response_body import UpdateApplicationRoleConnectionsMetadataHTTPResponseBody


class UpdateApplicationRoleConnectionsMetadataHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateApplicationRoleConnectionsMetadataHTTPResponseBody | None = None
    raw_body: bytes
