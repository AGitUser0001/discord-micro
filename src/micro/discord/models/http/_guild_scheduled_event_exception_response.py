# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class GuildScheduledEventExceptionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    event_id: Annotated[
        SnowflakeType,
        Field(description='ID of the scheduled event this exception belongs to'),
    ]
    event_exception_id: Annotated[
        SnowflakeType, Field(description='ID of the event exception')
    ]
    scheduled_start_time: Annotated[
        AwareDatetime | None,
        Field(description='Overridden start time of this occurrence'),
    ]
    scheduled_end_time: Annotated[
        AwareDatetime | None,
        Field(description='Overridden end time of this occurrence'),
    ]
    is_canceled: Annotated[
        bool, Field(description='Whether this occurrence is canceled')
    ]
