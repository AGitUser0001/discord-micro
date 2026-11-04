# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._applications_get_activity_instance_http_response_body import ApplicationsGetActivityInstanceHTTPResponseBody


class ApplicationsGetActivityInstanceHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: ApplicationsGetActivityInstanceHTTPResponseBody | None = None
  raw_body: bytes
