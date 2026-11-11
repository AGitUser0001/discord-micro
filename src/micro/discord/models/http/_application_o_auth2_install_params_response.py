# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._o_auth2_scopes import OAuth2Scopes


class ApplicationOAuth2InstallParamsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    scopes: list[OAuth2Scopes]
    permissions: str
