# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._bulk_set_guild_application_commands_http_response_body import BulkSetGuildApplicationCommandsHTTPResponseBody


class BulkSetGuildApplicationCommandsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkSetGuildApplicationCommandsHTTPResponseBody | None = None
  raw_body: bytes
