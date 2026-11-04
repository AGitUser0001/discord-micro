# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_application_emojis_http_response_body import ListApplicationEmojisHTTPResponseBody


class ListApplicationEmojisHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListApplicationEmojisHTTPResponseBody | None = None
  raw_body: bytes
