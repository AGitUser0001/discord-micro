# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._bulk_update_guild_roles_http_response_body import BulkUpdateGuildRolesHTTPResponseBody


class BulkUpdateGuildRolesHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkUpdateGuildRolesHTTPResponseBody | None = None
  raw_body: bytes
