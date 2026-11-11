# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_group_dm_user_http_response_body import DeleteGroupDmUserHTTPResponseBody


class DeleteGroupDmUserHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteGroupDmUserHTTPResponseBody | None = None
    raw_body: bytes
