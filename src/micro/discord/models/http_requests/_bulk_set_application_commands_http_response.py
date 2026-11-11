# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._bulk_set_application_commands_http_response_body import BulkSetApplicationCommandsHTTPResponseBody


class BulkSetApplicationCommandsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: BulkSetApplicationCommandsHTTPResponseBody | None = None
    raw_body: bytes
