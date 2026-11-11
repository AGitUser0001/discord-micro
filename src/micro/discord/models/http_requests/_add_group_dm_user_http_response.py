# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._add_group_dm_user_http_response_body import AddGroupDmUserHTTPResponseBody


class AddGroupDmUserHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: AddGroupDmUserHTTPResponseBody | None = None
    raw_body: bytes
