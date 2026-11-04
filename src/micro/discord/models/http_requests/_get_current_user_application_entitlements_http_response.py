# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_current_user_application_entitlements_http_response_body import GetCurrentUserApplicationEntitlementsHTTPResponseBody


class GetCurrentUserApplicationEntitlementsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetCurrentUserApplicationEntitlementsHTTPResponseBody | None = None
  raw_body: bytes
