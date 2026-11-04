# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._channel_types import ChannelTypes
from ._snowflake_type import SnowflakeType
from ._thread_metadata_response import ThreadMetadataResponse
from ._video_quality_modes import VideoQualityModes
from ._thread_member_response import ThreadMemberResponse


class CreatedThreadResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: ChannelTypes
    last_message_id: SnowflakeType | None = None
    flags: int
    last_pin_timestamp: AwareDatetime | None = None
    guild_id: SnowflakeType
    name: str
    parent_id: SnowflakeType | None = None
    rate_limit_per_user: int | None = None
    bitrate: int | None = None
    user_limit: int | None = None
    rtc_region: str | None = None
    video_quality_mode: VideoQualityModes | None = None
    permissions: str | None = None
    owner_id: SnowflakeType
    thread_metadata: ThreadMetadataResponse
    message_count: int
    member_count: int
    total_message_sent: int
    applied_tags: list[SnowflakeType] | None = None
    member: ThreadMemberResponse | None = None
