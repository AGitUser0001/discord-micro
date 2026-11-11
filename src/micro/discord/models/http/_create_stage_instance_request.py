# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._stage_instances_privacy_levels import StageInstancesPrivacyLevels


class CreateStageInstanceRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    topic: Annotated[str, Field(max_length=120, min_length=1)]
    channel_id: SnowflakeType
    privacy_level: StageInstancesPrivacyLevels | None = None
    guild_scheduled_event_id: SnowflakeType | None = None
    send_start_notification: bool | None = None
