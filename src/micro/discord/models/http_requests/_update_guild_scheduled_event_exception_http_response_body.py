# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class UpdateGuildScheduledEventExceptionHTTPResponseBody(
  RootModel[
    http.GuildScheduledEventExceptionResponse
    | http.RatelimitedResponse
    | http.ErrorResponse
  ]
):
  pass
