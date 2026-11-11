# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._status1 import Status1
from ._api_guild_scheduled_event_recurrence_rule import APIGuildScheduledEventRecurrenceRule
from ._api_user import APIUser


class APIVoiceGuildScheduledEvent(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the guild event')]
    guild_id: Annotated[
        str, Field(description='The guild id which the scheduled event belongs to')
    ]
    creator_id: Annotated[
        str | None,
        Field(description='The id of the user that created the scheduled event'),
    ] = None
    name: Annotated[str, Field(description='The name of the scheduled event')]
    description: Annotated[
        str | None, Field(description='The description of the scheduled event')
    ] = None
    scheduled_start_time: Annotated[
        str, Field(description='The time the scheduled event will start')
    ]
    scheduled_end_time: Annotated[
        str | None,
        Field(
            description='The time at which the guild event will end, or `null` if the event does not have a scheduled time to end'
        ),
    ]
    privacy_level: Annotated[
        Literal[2], Field(description='The privacy level of the scheduled event')
    ]
    status: Annotated[Status1, Field(description='The status of the scheduled event')]
    entity_type: Annotated[
        Literal[2],
        Field(
            description='The type of hosting entity associated with the scheduled event'
        ),
    ]
    entity_id: Annotated[
        str | None,
        Field(
            description='The id of the hosting entity associated with the scheduled event'
        ),
    ]
    creator: Annotated[
        APIUser | None, Field(description='The user that created the scheduled event')
    ] = None
    user_count: Annotated[
        float | None,
        Field(description='The number of users subscribed to the scheduled event'),
    ] = None
    image: Annotated[
        str | None, Field(description='The cover image of the scheduled event')
    ] = None
    recurrence_rule: Annotated[
        APIGuildScheduledEventRecurrenceRule | None,
        Field(description='The definition for how often this event should recur'),
    ]
    channel_id: str
    entity_metadata: None
