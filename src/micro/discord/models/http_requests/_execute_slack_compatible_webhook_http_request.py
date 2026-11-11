# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class ExecuteSlackCompatibleWebhookHTTPRequest(DiscordModel):
    path: http.ExecuteSlackCompatibleWebhookParametersPath
    query: http.ExecuteSlackCompatibleWebhookParametersQuery | None = None
    body: http.SlackWebhook
    content_type: str = "application/json"
