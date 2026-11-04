# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_invite_target_users_http_response_body import UpdateInviteTargetUsersHTTPResponseBody


class UpdateInviteTargetUsersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateInviteTargetUsersHTTPResponseBody | None = None
  raw_body: bytes
