# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._partner_sdk_token_http_response_body import PartnerSdkTokenHTTPResponseBody


class PartnerSdkTokenHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PartnerSdkTokenHTTPResponseBody | None = None
  raw_body: bytes
