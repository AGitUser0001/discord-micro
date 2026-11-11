# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_guild_application_command_http_response_body import CreateGuildApplicationCommandHTTPResponseBody


class CreateGuildApplicationCommandHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateGuildApplicationCommandHTTPResponseBody | None = None
    raw_body: bytes
