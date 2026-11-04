# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http

from ._put_guilds_onboarding_http_response_body import PutGuildsOnboardingHTTPResponseBody


class PutGuildsOnboardingHTTPResponse(DiscordModel):
  status: int
  headers: tuple[tuple[str, str], ...]
  body: PutGuildsOnboardingHTTPResponseBody | None = None
  raw_body: bytes
