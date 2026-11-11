# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class ListGuildApplicationCommandPermissionsHTTPResponseBody(
    RootModel[
        http.ListGuildApplicationCommandPermissionsResponse200
        | http.RatelimitedResponse
        | http.ErrorResponse
    ]
):
    pass
