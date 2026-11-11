# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._create_dm_http_response_body import CreateDmHTTPResponseBody


class CreateDmHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: CreateDmHTTPResponseBody | None = None
    raw_body: bytes
