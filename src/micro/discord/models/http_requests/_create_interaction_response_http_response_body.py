# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class CreateInteractionResponseHTTPResponseBody(
    RootModel[
        http.InteractionCallbackResponse | http.RatelimitedResponse | http.ErrorResponse
    ]
):
    pass
