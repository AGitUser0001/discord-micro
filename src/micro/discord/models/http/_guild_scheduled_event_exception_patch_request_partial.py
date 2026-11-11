# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class GuildScheduledEventExceptionPatchRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    scheduled_start_time: Annotated[
        AwareDatetime | None,
        Field(description='Overridden start time of this occurrence'),
    ] = None
    scheduled_end_time: Annotated[
        AwareDatetime | None,
        Field(description='Overridden end time of this occurrence'),
    ] = None
    is_canceled: Annotated[
        bool | None, Field(description='Whether this occurrence is canceled')
    ] = None
