# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class BulkUpdateGuildChannelsHTTPRequest(DiscordModel):
  path: http.BulkUpdateGuildChannelsParametersPath
  body: http.BulkUpdateGuildChannelsRequest
  content_type: str = 'application/json'
