# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class UpdateApplicationRoleConnectionsMetadataHTTPRequest(DiscordModel):
    path: http.UpdateApplicationRoleConnectionsMetadataParametersPath
    body: http.UpdateApplicationRoleConnectionsMetadataRequest
    content_type: str = "application/json"
