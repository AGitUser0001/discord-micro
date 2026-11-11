# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_entitlement_http_response_body import DeleteEntitlementHTTPResponseBody


class DeleteEntitlementHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteEntitlementHTTPResponseBody | None = None
    raw_body: bytes
