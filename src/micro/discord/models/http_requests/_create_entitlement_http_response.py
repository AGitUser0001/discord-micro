# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._create_entitlement_http_response_body import CreateEntitlementHTTPResponseBody


class CreateEntitlementHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateEntitlementHTTPResponseBody | None = None
  raw_body: bytes
