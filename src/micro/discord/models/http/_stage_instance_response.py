# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._stage_instances_privacy_levels import StageInstancesPrivacyLevels


class StageInstanceResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: SnowflakeType
    channel_id: SnowflakeType
    topic: str
    privacy_level: StageInstancesPrivacyLevels
    id: SnowflakeType
    discoverable_disabled: bool
    guild_scheduled_event_id: SnowflakeType | None
