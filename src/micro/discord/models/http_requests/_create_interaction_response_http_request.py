# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class CreateInteractionResponseHTTPRequest(DiscordModel):
    path: http.CreateInteractionResponseParametersPath
    query: http.CreateInteractionResponseParametersQuery | None = None
    body: http.CreateInteractionResponseRequest
    content_type: str = "application/json"
