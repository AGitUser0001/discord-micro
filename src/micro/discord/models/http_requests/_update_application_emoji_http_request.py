# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class UpdateApplicationEmojiHTTPRequest(DiscordModel):
  path: http.UpdateApplicationEmojiParametersPath
  body: http.UpdateApplicationEmojiRequest
  content_type: str = 'application/json'
