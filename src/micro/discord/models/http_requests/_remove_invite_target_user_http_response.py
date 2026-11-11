# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._remove_invite_target_user_http_response_body import RemoveInviteTargetUserHTTPResponseBody


class RemoveInviteTargetUserHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: RemoveInviteTargetUserHTTPResponseBody | None = None
    raw_body: bytes
