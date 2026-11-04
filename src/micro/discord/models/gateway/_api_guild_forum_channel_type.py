# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags import Flags
from ._api_overwrite import APIOverwrite
from ._default_auto_archive_duration import DefaultAutoArchiveDuration
from ._default_sort_order import DefaultSortOrder
from ._default_forum_layout import DefaultForumLayout
from ._api_guild_forum_tag import APIGuildForumTag
from ._api_guild_forum_default_reaction_emoji import APIGuildForumDefaultReactionEmoji


class APIGuildForumChannelType(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    type: Annotated[
        Literal[15], Field(description='A channel that can only contain threads')
    ]
    flags: Flags | None = None
    position: Annotated[float, Field(description='Sorting position of the channel')]
    name: Annotated[
        str, Field(description='The name of the channel (1-100 characters)')
    ]
    guild_id: Annotated[
        str,
        Field(
            description='The id of the guild (may be missing for some channel objects received over gateway guild dispatches)'
        ),
    ]
    permission_overwrites: Annotated[
        list[APIOverwrite] | None,
        Field(description='Explicit permission overwrites for members and roles'),
    ] = None
    parent_id: Annotated[
        str | None,
        Field(
            description='ID of the parent category for a channel (each parent category can contain up to 50 channels)'
        ),
    ] = None
    nsfw: Annotated[bool | None, Field(description='Whether the channel is nsfw')] = (
        None
    )
    topic: Annotated[
        str | None, Field(description='The channel topic (0-4096 characters)')
    ] = None
    last_message_id: Annotated[
        str | None,
        Field(
            description='The id of the last thread created in this channel (may not point to an existing or valid thread)'
        ),
    ] = None
    rate_limit_per_user: Annotated[
        float | None,
        Field(
            description='Amount of seconds a user has to wait before creating another thread (0-21600);\nbots, as well as users with the permission `BYPASS_SLOWMODE`, are unaffected\n\nThe absence of this field in API calls and Gateway events should indicate that slowmode has been reset to the default value.'
        ),
    ] = None
    last_pin_timestamp: Annotated[
        str | None,
        Field(
            description='When the last pinned message was pinned.\nThis may be `null` in events such as `GUILD_CREATE` when a message is not pinned'
        ),
    ] = None
    default_auto_archive_duration: Annotated[
        DefaultAutoArchiveDuration | None,
        Field(
            description='Default duration for newly created threads, in minutes, to automatically archive the thread after recent activity'
        ),
    ] = None
    available_tags: Annotated[
        list[APIGuildForumTag],
        Field(description='The set of tags that can be used in a thread-only channel'),
    ]
    default_thread_rate_limit_per_user: Annotated[
        float | None,
        Field(
            description='The initial `rate_limit_per_user` to set on newly created threads.\nThis field is copied to the thread at creation time and does not live update'
        ),
    ] = None
    default_reaction_emoji: Annotated[
        APIGuildForumDefaultReactionEmoji | None,
        Field(
            description='The emoji to show in the add reaction button on a thread in a thread-only channel'
        ),
    ]
    default_sort_order: Annotated[
        DefaultSortOrder | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ]
    default_forum_layout: Annotated[
        DefaultForumLayout,
        Field(
            description='The default layout type used to display posts in a forum channel'
        ),
    ]
