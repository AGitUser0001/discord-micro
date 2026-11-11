# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._entity_metadata_stage_instance_response import EntityMetadataStageInstanceResponse
from ._guild_scheduled_event_entity_types import GuildScheduledEventEntityTypes
from ._guild_scheduled_event_privacy_levels import GuildScheduledEventPrivacyLevels
from ._guild_scheduled_event_statuses import GuildScheduledEventStatuses
from ._snowflake_type import SnowflakeType
from ._guild_scheduled_event_exception_response import GuildScheduledEventExceptionResponse
from ._recurrence_rule_response import RecurrenceRuleResponse
from ._user_response import UserResponse
from ._scheduled_event_user_response import ScheduledEventUserResponse


class StageScheduledEventResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[SnowflakeType, Field(description='ID of the scheduled event')]
    guild_id: Annotated[
        SnowflakeType,
        Field(description='ID of the guild the scheduled event belongs to'),
    ]
    name: Annotated[str, Field(description='Name of the scheduled event')]
    description: Annotated[
        str | None, Field(description='Description of the scheduled event')
    ]
    channel_id: Annotated[
        SnowflakeType | None,
        Field(
            description='Channel ID in which the scheduled event will be hosted, or null if entity type is EXTERNAL'
        ),
    ]
    creator_id: Annotated[
        SnowflakeType | None,
        Field(description='ID of the user that created the scheduled event'),
    ]
    creator: Annotated[
        UserResponse | None, Field(description='User that created the scheduled event')
    ] = None
    image: Annotated[
        str | None, Field(description='Cover image hash of the scheduled event')
    ]
    scheduled_start_time: Annotated[
        AwareDatetime, Field(description='When the scheduled event will start')
    ]
    scheduled_end_time: Annotated[
        AwareDatetime | None,
        Field(description='When the scheduled event will end, or null if no end time'),
    ]
    status: Annotated[
        GuildScheduledEventStatuses, Field(description='Status of the scheduled event')
    ]
    entity_type: Annotated[
        GuildScheduledEventEntityTypes,
        Field(description='Type of hosting entity associated with the scheduled event'),
    ]
    entity_id: Annotated[
        SnowflakeType | None,
        Field(
            description='ID of the hosting entity associated with the scheduled event'
        ),
    ]
    recurrence_rule: Annotated[
        RecurrenceRuleResponse | None,
        Field(
            description='Recurrence rule for the scheduled event, or null if not recurring'
        ),
    ]
    user_count: Annotated[
        int | None,
        Field(description='Number of users subscribed to the scheduled event'),
    ] = None
    privacy_level: Annotated[
        GuildScheduledEventPrivacyLevels,
        Field(description='Privacy level of the scheduled event'),
    ]
    user_rsvp: ScheduledEventUserResponse | None = None
    guild_scheduled_event_exceptions: list[GuildScheduledEventExceptionResponse]
    entity_metadata: EntityMetadataStageInstanceResponse | None
