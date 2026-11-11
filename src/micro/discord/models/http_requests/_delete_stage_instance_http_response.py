# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._delete_stage_instance_http_response_body import DeleteStageInstanceHTTPResponseBody


class DeleteStageInstanceHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: DeleteStageInstanceHTTPResponseBody | None = None
    raw_body: bytes
