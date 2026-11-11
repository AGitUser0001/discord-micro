# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_thread_members_http_response_body import ListThreadMembersHTTPResponseBody


class ListThreadMembersHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListThreadMembersHTTPResponseBody | None = None
    raw_body: bytes
