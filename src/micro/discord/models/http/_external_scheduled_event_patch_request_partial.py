# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._entity_metadata_external import EntityMetadataExternal
from ._guild_scheduled_event_entity_types import GuildScheduledEventEntityTypes
from ._guild_scheduled_event_privacy_levels import GuildScheduledEventPrivacyLevels
from ._guild_scheduled_event_statuses import GuildScheduledEventStatuses
from ._snowflake_type import SnowflakeType
from ._recurrence_rule import RecurrenceRule


class ExternalScheduledEventPatchRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    status: GuildScheduledEventStatuses | None = None
    name: Annotated[str | None, Field(max_length=100)] = None
    description: Annotated[str | None, Field(max_length=1000)] = None
    image: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    scheduled_start_time: AwareDatetime | None = None
    scheduled_end_time: AwareDatetime | None = None
    entity_type: GuildScheduledEventEntityTypes | None = None
    privacy_level: GuildScheduledEventPrivacyLevels | None = None
    channel_id: SnowflakeType | None = None
    recurrence_rule: Annotated[
        RecurrenceRule | None,
        Field(description='Recurrence rule for the scheduled event'),
    ] = None
    entity_metadata: EntityMetadataExternal | None = None
