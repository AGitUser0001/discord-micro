# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class CreateAutoModerationRuleHTTPRequest(DiscordModel):
  path: http.CreateAutoModerationRuleParametersPath
  body: http.CreateAutoModerationRuleRequest
  content_type: str = 'application/json'
