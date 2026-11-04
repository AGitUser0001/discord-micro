# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._o_auth2_scopes import OAuth2Scopes
from ._user_response import UserResponse
from ._application_response import ApplicationResponse


class OAuth2GetAuthorizationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    application: ApplicationResponse
    expires: AwareDatetime
    scopes: list[OAuth2Scopes]
    user: UserResponse | None = None
