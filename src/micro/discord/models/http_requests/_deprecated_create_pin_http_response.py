# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._deprecated_create_pin_http_response_body import DeprecatedCreatePinHTTPResponseBody


class DeprecatedCreatePinHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: DeprecatedCreatePinHTTPResponseBody | None = None
  raw_body: bytes
