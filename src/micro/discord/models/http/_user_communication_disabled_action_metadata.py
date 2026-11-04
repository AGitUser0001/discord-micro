# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class UserCommunicationDisabledActionMetadata(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    duration_seconds: Annotated[int | None, Field(ge=0, le=2419200)] = None
