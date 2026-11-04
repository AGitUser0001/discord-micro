# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class ListGuildScheduledEventUsersHTTPResponseBody(
  RootModel[
    http.ListGuildScheduledEventUsersResponse200
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass
