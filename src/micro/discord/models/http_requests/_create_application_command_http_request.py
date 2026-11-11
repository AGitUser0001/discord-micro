# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class CreateApplicationCommandHTTPRequest(DiscordModel):
    path: http.CreateApplicationCommandParametersPath
    body: http.ApplicationCommandCreateRequest
    content_type: str = "application/json"
