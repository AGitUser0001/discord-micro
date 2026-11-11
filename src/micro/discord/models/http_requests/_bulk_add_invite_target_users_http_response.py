# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._bulk_add_invite_target_users_http_response_body import BulkAddInviteTargetUsersHTTPResponseBody


class BulkAddInviteTargetUsersHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: BulkAddInviteTargetUsersHTTPResponseBody | None = None
    raw_body: bytes
