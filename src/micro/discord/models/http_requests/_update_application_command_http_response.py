# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_application_command_http_response_body import UpdateApplicationCommandHTTPResponseBody


class UpdateApplicationCommandHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateApplicationCommandHTTPResponseBody | None = None
    raw_body: bytes
