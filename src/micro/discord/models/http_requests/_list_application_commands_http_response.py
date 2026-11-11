# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._list_application_commands_http_response_body import ListApplicationCommandsHTTPResponseBody


class ListApplicationCommandsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: ListApplicationCommandsHTTPResponseBody | None = None
    raw_body: bytes
