# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_thread_member_http_response_body import DeleteThreadMemberHTTPResponseBody


class DeleteThreadMemberHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteThreadMemberHTTPResponseBody | None = None
    raw_body: bytes
