# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._bulk_update_guild_channels_http_response_body import BulkUpdateGuildChannelsHTTPResponseBody


class BulkUpdateGuildChannelsHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: BulkUpdateGuildChannelsHTTPResponseBody | None = None
  raw_body: bytes
