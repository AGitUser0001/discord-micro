# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._get_answer_voters_http_response_body import GetAnswerVotersHTTPResponseBody


class GetAnswerVotersHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: GetAnswerVotersHTTPResponseBody | None = None
  raw_body: bytes
