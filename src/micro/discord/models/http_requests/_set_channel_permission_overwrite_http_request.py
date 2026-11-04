# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class SetChannelPermissionOverwriteHTTPRequest(DiscordModel):
  path: http.SetChannelPermissionOverwriteParametersPath
  body: http.SetChannelPermissionOverwriteRequest
  content_type: str = 'application/json'
