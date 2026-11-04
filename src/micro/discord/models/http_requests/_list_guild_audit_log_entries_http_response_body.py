# Generated from Discord's API specification. Do not edit directly.

from pydantic import RootModel
from micro.discord._model import DiscordModel
from micro.discord.models import http



class ListGuildAuditLogEntriesHTTPResponseBody(
  RootModel[http.GuildAuditLogResponse | http.RatelimitedResponse | http.ErrorResponse]
):
  pass
