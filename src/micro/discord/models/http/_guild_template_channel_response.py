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
from ._channel_permission_overwrite_response import ChannelPermissionOverwriteResponse
from ._default_reaction_emoji_response import DefaultReactionEmojiResponse
from ._guild_template_channel_tags import GuildTemplateChannelTags


class GuildTemplateChannelResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: int | None
    type: ChannelTypes
    name: str | None
    position: int | None
    topic: str | None
    bitrate: int
    user_limit: int
    nsfw: bool
    rate_limit_per_user: int
    parent_id: SnowflakeType | None
    default_auto_archive_duration: ThreadAutoArchiveDuration | None
    permission_overwrites: list[ChannelPermissionOverwriteResponse]
    available_tags: list[GuildTemplateChannelTags] | None
    template: str
    default_reaction_emoji: DefaultReactionEmojiResponse | None
    default_thread_rate_limit_per_user: int | None
    default_sort_order: ThreadSortOrder | None
    default_forum_layout: ForumLayout | None
    default_tag_setting: ThreadSearchTagSetting | None
    theme_color: int | None
