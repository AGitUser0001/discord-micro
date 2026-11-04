# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class ExecuteGithubCompatibleWebhookHTTPRequest(DiscordModel):
  path: http.ExecuteGithubCompatibleWebhookParametersPath
  query: http.ExecuteGithubCompatibleWebhookParametersQuery | None = None
  body: http.GithubWebhook
  content_type: str = 'application/json'
