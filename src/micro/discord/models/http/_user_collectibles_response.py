# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._user_nameplate_response import UserNameplateResponse


class UserCollectiblesResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    nameplate: Annotated[
        UserNameplateResponse | None,
        Field(description='Object mapping of nameplate data'),
    ]
