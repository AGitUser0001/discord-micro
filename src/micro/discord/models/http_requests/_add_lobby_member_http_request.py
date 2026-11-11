# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class AddLobbyMemberHTTPRequest(DiscordModel):
    path: http.AddLobbyMemberParametersPath
    body: http.AddLobbyMemberRequest
    content_type: str = "application/json"
