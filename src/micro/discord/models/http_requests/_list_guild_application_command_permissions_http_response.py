# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._list_guild_application_command_permissions_http_response_body import ListGuildApplicationCommandPermissionsHTTPResponseBody


class ListGuildApplicationCommandPermissionsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ListGuildApplicationCommandPermissionsHTTPResponseBody | None = None
  raw_body: bytes
