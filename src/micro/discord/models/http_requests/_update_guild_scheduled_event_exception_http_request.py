# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class UpdateGuildScheduledEventExceptionHTTPRequest(DiscordModel):
  path: http.UpdateGuildScheduledEventExceptionParametersPath
  body: http.GuildScheduledEventExceptionPatchRequestPartial
  content_type: str = 'application/json'
