# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class BulkUpdateGuildRolesHTTPRequest(DiscordModel):
    path: http.BulkUpdateGuildRolesParametersPath
    body: http.BulkUpdateGuildRolesRequest
    content_type: str = "application/json"
