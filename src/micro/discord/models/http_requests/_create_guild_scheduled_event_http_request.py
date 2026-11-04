# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class CreateGuildScheduledEventHTTPRequest(DiscordModel):
  path: http.CreateGuildScheduledEventParametersPath
  body: http.CreateGuildScheduledEventRequest
  content_type: str = 'application/json'
