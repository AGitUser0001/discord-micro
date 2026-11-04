# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._bulk_delete_messages_http_response_body import BulkDeleteMessagesHTTPResponseBody


class BulkDeleteMessagesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkDeleteMessagesHTTPResponseBody | None = None
  raw_body: bytes
