# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._consume_entitlement_http_response_body import ConsumeEntitlementHTTPResponseBody


class ConsumeEntitlementHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ConsumeEntitlementHTTPResponseBody | None = None
    raw_body: bytes
