# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ScheduledEventUserCountResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_scheduled_event_count: Annotated[
        int, Field(description='The number of users subscribed to the scheduled event')
    ]
    guild_scheduled_event_exception_counts: Annotated[
        dict[str, int],
        Field(description='Map of exception IDs to user counts for each exception'),
    ]
