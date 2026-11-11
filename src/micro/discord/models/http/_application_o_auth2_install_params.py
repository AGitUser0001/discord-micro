# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._o_auth2_scopes import OAuth2Scopes


class ApplicationOAuth2InstallParams(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    scopes: Annotated[list[OAuth2Scopes] | None, Field(min_length=1)] = None
    permissions: Annotated[int | None, Field(ge=0, le=18014398509481983)] = None
