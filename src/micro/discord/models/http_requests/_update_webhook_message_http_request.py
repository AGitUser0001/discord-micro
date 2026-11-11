# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class UpdateWebhookMessageHTTPRequest(DiscordModel):
    path: http.UpdateWebhookMessageParametersPath
    query: http.UpdateWebhookMessageParametersQuery | None = None
    body: http.UpdateWebhookMessageRequest
    content_type: str = "application/json"
