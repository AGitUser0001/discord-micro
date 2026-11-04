# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_invite_target_users_job_status_http_response_body import GetInviteTargetUsersJobStatusHTTPResponseBody


class GetInviteTargetUsersJobStatusHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetInviteTargetUsersJobStatusHTTPResponseBody | None = None
  raw_body: bytes
