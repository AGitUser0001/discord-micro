# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._entity_metadata_voice import EntityMetadataVoice
from ._guild_scheduled_event_entity_types import GuildScheduledEventEntityTypes
from ._guild_scheduled_event_privacy_levels import GuildScheduledEventPrivacyLevels
from ._snowflake_type import SnowflakeType
from ._recurrence_rule import RecurrenceRule


class VoiceScheduledEventCreateRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(max_length=100)]
    description: Annotated[str | None, Field(max_length=1000)] = None
    image: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    scheduled_start_time: AwareDatetime
    scheduled_end_time: AwareDatetime | None = None
    privacy_level: GuildScheduledEventPrivacyLevels
    entity_type: GuildScheduledEventEntityTypes
    channel_id: SnowflakeType | None = None
    recurrence_rule: Annotated[
        RecurrenceRule | None,
        Field(description='Recurrence rule for the scheduled event'),
    ] = None
    entity_metadata: EntityMetadataVoice | None = None
