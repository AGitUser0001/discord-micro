# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_my_user_http_response_body import UpdateMyUserHTTPResponseBody


class UpdateMyUserHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateMyUserHTTPResponseBody | None = None
    raw_body: bytes
