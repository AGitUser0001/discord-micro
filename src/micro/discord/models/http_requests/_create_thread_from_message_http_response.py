# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._create_thread_from_message_http_response_body import CreateThreadFromMessageHTTPResponseBody


class CreateThreadFromMessageHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: CreateThreadFromMessageHTTPResponseBody | None = None
  raw_body: bytes
