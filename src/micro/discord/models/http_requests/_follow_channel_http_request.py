# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class FollowChannelHTTPRequest(DiscordModel):
    path: http.FollowChannelParametersPath
    body: http.FollowChannelRequest
    content_type: str = "application/json"
