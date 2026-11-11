# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class UpdateGuildTemplateHTTPRequest(DiscordModel):
    path: http.UpdateGuildTemplateParametersPath
    body: http.UpdateGuildTemplateRequest
    content_type: str = "application/json"
