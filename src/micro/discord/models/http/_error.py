# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class Error(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    code: Annotated[
        int, Field(description='Discord internal error code. See error code reference')
    ]
    message: Annotated[str, Field(description='Human-readable error message')]
