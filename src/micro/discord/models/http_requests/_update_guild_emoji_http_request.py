# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class UpdateGuildEmojiHTTPRequest(DiscordModel):
    path: http.UpdateGuildEmojiParametersPath
    body: http.UpdateGuildEmojiRequest
    content_type: str = "application/json"
