# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class CreateWebhookHTTPRequest(DiscordModel):
  path: http.CreateWebhookParametersPath
  body: http.CreateWebhookRequest
  content_type: str = 'application/json'
