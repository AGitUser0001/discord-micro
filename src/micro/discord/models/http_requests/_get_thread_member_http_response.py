# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_thread_member_http_response_body import GetThreadMemberHTTPResponseBody


class GetThreadMemberHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetThreadMemberHTTPResponseBody | None = None
    raw_body: bytes
