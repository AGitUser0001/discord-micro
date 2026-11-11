# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class DeleteOriginalWebhookMessageHTTPRequest(DiscordModel):
    path: http.DeleteOriginalWebhookMessageParametersPath
    query: http.DeleteOriginalWebhookMessageParametersQuery | None = None
