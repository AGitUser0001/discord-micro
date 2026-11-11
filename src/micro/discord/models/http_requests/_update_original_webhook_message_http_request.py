# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class UpdateOriginalWebhookMessageHTTPRequest(DiscordModel):
    path: http.UpdateOriginalWebhookMessageParametersPath
    query: http.UpdateOriginalWebhookMessageParametersQuery | None = None
    body: http.UpdateOriginalWebhookMessageRequest
    content_type: str = "application/json"
