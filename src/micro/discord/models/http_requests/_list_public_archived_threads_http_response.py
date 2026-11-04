# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_public_archived_threads_http_response_body import ListPublicArchivedThreadsHTTPResponseBody


class ListPublicArchivedThreadsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListPublicArchivedThreadsHTTPResponseBody | None = None
  raw_body: bytes
