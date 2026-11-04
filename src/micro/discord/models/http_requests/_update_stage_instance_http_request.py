# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class UpdateStageInstanceHTTPRequest(DiscordModel):
  path: http.UpdateStageInstanceParametersPath
  body: http.UpdateStageInstanceRequest
  content_type: str = 'application/json'
