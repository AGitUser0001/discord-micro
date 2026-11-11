# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_my_connections_http_response_body import ListMyConnectionsHTTPResponseBody


class ListMyConnectionsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListMyConnectionsHTTPResponseBody | None = None
    raw_body: bytes
