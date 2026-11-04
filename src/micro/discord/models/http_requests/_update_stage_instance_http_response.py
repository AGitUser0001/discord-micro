# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._update_stage_instance_http_response_body import UpdateStageInstanceHTTPResponseBody


class UpdateStageInstanceHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: UpdateStageInstanceHTTPResponseBody | None = None
  raw_body: bytes
