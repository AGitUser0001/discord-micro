# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class GetChannelRolePermissionsHTTPRequest(DiscordModel):
    path: http.GetChannelRolePermissionsParametersPath
    query: http.GetChannelRolePermissionsParametersQuery | None = None
