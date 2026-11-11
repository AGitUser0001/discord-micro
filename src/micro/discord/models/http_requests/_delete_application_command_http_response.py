# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_application_command_http_response_body import DeleteApplicationCommandHTTPResponseBody


class DeleteApplicationCommandHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteApplicationCommandHTTPResponseBody | None = None
    raw_body: bytes
