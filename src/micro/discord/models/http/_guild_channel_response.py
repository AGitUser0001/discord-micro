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
from ._video_quality_modes import VideoQualityModes
from ._channel_permission_overwrite_response import ChannelPermissionOverwriteResponse
from ._default_reaction_emoji_response import DefaultReactionEmojiResponse
from ._forum_tag_response import ForumTagResponse


class GuildChannelResponse(DiscordModel):
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
    topic: str | None = None
    default_auto_archive_duration: ThreadAutoArchiveDuration | None = None
    default_thread_rate_limit_per_user: int | None = None
    position: int
    permission_overwrites: list[ChannelPermissionOverwriteResponse] | None = None
    nsfw: bool | None = None
    available_tags: list[ForumTagResponse] | None = None
    default_reaction_emoji: DefaultReactionEmojiResponse | None = None
    default_sort_order: ThreadSortOrder | None = None
    default_forum_layout: ForumLayout | None = None
    default_tag_setting: ThreadSearchTagSetting | None = None
