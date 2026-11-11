# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._get_stage_instance_http_response_body import GetStageInstanceHTTPResponseBody


class GetStageInstanceHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: GetStageInstanceHTTPResponseBody | None = None
    raw_body: bytes
