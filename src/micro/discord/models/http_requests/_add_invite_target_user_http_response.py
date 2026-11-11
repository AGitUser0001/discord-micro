# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._add_invite_target_user_http_response_body import AddInviteTargetUserHTTPResponseBody


class AddInviteTargetUserHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: AddInviteTargetUserHTTPResponseBody | None = None
    raw_body: bytes
