# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._poll_expire_http_response_body import PollExpireHTTPResponseBody


class PollExpireHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PollExpireHTTPResponseBody | None = None
  raw_body: bytes
