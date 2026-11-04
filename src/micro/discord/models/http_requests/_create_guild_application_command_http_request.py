# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class CreateGuildApplicationCommandHTTPRequest(DiscordModel):
  path: http.CreateGuildApplicationCommandParametersPath
  body: http.ApplicationCommandCreateRequest
  content_type: str = 'application/json'
