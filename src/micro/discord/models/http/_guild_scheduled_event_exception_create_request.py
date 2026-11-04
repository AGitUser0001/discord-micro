# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class GuildScheduledEventExceptionCreateRequest(DiscordModel):
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
    original_scheduled_start_time: Annotated[
        AwareDatetime,
        Field(
            description='The original start time of the occurrence to create an exception for'
        ),
    ]
    is_canceled: Annotated[
        bool | None, Field(description='Whether this occurrence is canceled')
    ] = None
