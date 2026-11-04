# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._set_guild_application_command_permissions_http_response_body import SetGuildApplicationCommandPermissionsHTTPResponseBody


class SetGuildApplicationCommandPermissionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: SetGuildApplicationCommandPermissionsHTTPResponseBody | None = None
  raw_body: bytes
