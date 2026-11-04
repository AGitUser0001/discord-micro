# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._channel_types import ChannelTypes
from ._forum_layout import ForumLayout
from ._snowflake_type import SnowflakeType
from ._thread_auto_archive_duration import ThreadAutoArchiveDuration
from ._thread_search_tag_setting import ThreadSearchTagSetting
from ._thread_sort_order import ThreadSortOrder
from ._update_default_reaction_emoji_request import UpdateDefaultReactionEmojiRequest
from ._video_quality_modes import VideoQualityModes
from ._channel_permission_overwrite_request import ChannelPermissionOverwriteRequest
from ._create_or_update_thread_tag_request import CreateOrUpdateThreadTagRequest


class CreateGuildChannelRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: ChannelTypes | None = None
    name: Annotated[str, Field(max_length=100, min_length=1)]
    position: Annotated[int | None, Field(ge=0)] = None
    topic: Annotated[str | None, Field(max_length=4096, min_length=0)] = None
    bitrate: Annotated[int | None, Field(ge=8000)] = None
    user_limit: Annotated[int | None, Field(ge=0)] = None
    nsfw: bool | None = None
    rate_limit_per_user: Annotated[int | None, Field(ge=0, le=21600)] = None
    parent_id: SnowflakeType | None = None
    permission_overwrites: Annotated[
        list[ChannelPermissionOverwriteRequest] | None, Field(max_length=100)
    ] = None
    rtc_region: str | None = None
    video_quality_mode: VideoQualityModes | None = None
    default_auto_archive_duration: ThreadAutoArchiveDuration | None = None
    default_reaction_emoji: UpdateDefaultReactionEmojiRequest | None = None
    default_thread_rate_limit_per_user: Annotated[int | None, Field(ge=0, le=21600)] = (
        None
    )
    default_sort_order: ThreadSortOrder | None = None
    default_forum_layout: ForumLayout | None = None
    default_tag_setting: ThreadSearchTagSetting | None = None
    available_tags: Annotated[
        list[CreateOrUpdateThreadTagRequest | None] | None, Field(max_length=20)
    ] = None
