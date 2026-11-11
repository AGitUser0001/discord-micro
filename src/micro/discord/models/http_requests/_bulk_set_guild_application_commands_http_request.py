# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class BulkSetGuildApplicationCommandsHTTPRequest(DiscordModel):
    path: http.BulkSetGuildApplicationCommandsParametersPath
    body: http.BulkSetGuildApplicationCommandsRequest
    content_type: str = "application/json"
