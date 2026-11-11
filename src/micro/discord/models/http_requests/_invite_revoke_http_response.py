# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._invite_revoke_http_response_body import InviteRevokeHTTPResponseBody


class InviteRevokeHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: InviteRevokeHTTPResponseBody | None = None
    raw_body: bytes
