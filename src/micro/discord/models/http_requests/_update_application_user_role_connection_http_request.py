# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class UpdateApplicationUserRoleConnectionHTTPRequest(DiscordModel):
  path: http.UpdateApplicationUserRoleConnectionParametersPath
  body: http.UpdateApplicationUserRoleConnectionRequest
  content_type: str = 'application/json'
