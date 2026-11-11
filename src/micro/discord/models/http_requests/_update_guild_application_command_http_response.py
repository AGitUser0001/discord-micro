# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_guild_application_command_http_response_body import UpdateGuildApplicationCommandHTTPResponseBody


class UpdateGuildApplicationCommandHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateGuildApplicationCommandHTTPResponseBody | None = None
    raw_body: bytes
