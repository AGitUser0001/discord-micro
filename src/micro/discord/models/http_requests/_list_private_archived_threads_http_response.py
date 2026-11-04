# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_private_archived_threads_http_response_body import ListPrivateArchivedThreadsHTTPResponseBody


class ListPrivateArchivedThreadsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListPrivateArchivedThreadsHTTPResponseBody | None = None
  raw_body: bytes
