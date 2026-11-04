# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._join_thread_http_response_body import JoinThreadHTTPResponseBody


class JoinThreadHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: JoinThreadHTTPResponseBody | None = None
  raw_body: bytes
