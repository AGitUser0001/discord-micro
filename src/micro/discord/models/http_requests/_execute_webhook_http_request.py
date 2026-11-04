# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class ExecuteWebhookHTTPRequest(DiscordModel):
  path: http.ExecuteWebhookParametersPath
  query: http.ExecuteWebhookParametersQuery | None = None
  body: http.ExecuteWebhookRequest
  content_type: str = 'application/json'
