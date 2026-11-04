# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class UpdateVoiceStateHTTPRequest(DiscordModel):
  path: http.UpdateVoiceStateParametersPath
  body: http.UpdateVoiceStateRequestPartial
  content_type: str = 'application/json'
