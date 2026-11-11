# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http

from ._update_guild_incident_actions_http_response_body import UpdateGuildIncidentActionsHTTPResponseBody


class UpdateGuildIncidentActionsHTTPResponse(DiscordModel):
    status: int
    headers: tuple[tuple[str, str], ...]
    body: UpdateGuildIncidentActionsHTTPResponseBody | None = None
    raw_body: bytes
