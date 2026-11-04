# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._thread_auto_archive_duration import ThreadAutoArchiveDuration
from ._video_quality_modes import VideoQualityModes


class UpdateThreadRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str | None, Field(max_length=100, min_length=0)] = None
    archived: bool | None = None
    locked: bool | None = None
    invitable: bool | None = None
    auto_archive_duration: ThreadAutoArchiveDuration | None = None
    rate_limit_per_user: Annotated[int | None, Field(ge=0, le=21600)] = None
    flags: int | None = None
    applied_tags: Annotated[list[SnowflakeType] | None, Field(max_length=5)] = None
    bitrate: Annotated[int | None, Field(ge=8000)] = None
    user_limit: Annotated[int | None, Field(ge=0, le=99)] = None
    rtc_region: str | None = None
    video_quality_mode: VideoQualityModes | None = None
