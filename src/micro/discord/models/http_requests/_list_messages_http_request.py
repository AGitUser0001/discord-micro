# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class ListMessagesHTTPRequest(DiscordModel):
  path: http.ListMessagesParametersPath
  query: http.ListMessagesParametersQuery | None = None
