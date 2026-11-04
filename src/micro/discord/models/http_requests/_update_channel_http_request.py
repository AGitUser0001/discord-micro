# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class UpdateChannelHTTPRequest(DiscordModel):
  path: http.UpdateChannelParametersPath
  body: http.UpdateChannelRequest
  content_type: str = 'application/json'
