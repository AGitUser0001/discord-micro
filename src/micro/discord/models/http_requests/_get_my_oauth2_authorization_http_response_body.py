# Generated from Discord's API specification. Do not edit directly.

from micro.discord._model import DiscordModel
from pydantic import RootModel
from micro.discord.models import http



class GetMyOauth2AuthorizationHTTPResponseBody(
    RootModel[
        http.OAuth2GetAuthorizationResponse
        | http.RatelimitedResponse
        | http.ErrorResponse
    ]
):
    pass
