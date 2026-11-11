# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._add_thread_member_http_response_body import AddThreadMemberHTTPResponseBody


class AddThreadMemberHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: AddThreadMemberHTTPResponseBody | None = None
    raw_body: bytes
