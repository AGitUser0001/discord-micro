# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._prune_guild_http_response_body import PruneGuildHTTPResponseBody


class PruneGuildHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: PruneGuildHTTPResponseBody | None = None
    raw_body: bytes
