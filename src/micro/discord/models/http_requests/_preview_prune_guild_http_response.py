# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._preview_prune_guild_http_response_body import PreviewPruneGuildHTTPResponseBody


class PreviewPruneGuildHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: PreviewPruneGuildHTTPResponseBody | None = None
    raw_body: bytes
