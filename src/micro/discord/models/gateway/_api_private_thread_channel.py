# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_overwrite import APIOverwrite
from ._api_thread_metadata import APIThreadMetadata
from ._flags41 import Flags41
from ._api_thread_member import APIThreadMember


class APIPrivateThreadChannel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    type: Annotated[
        Literal[12],
        Field(
            description='A temporary sub-channel within a Guild Text channel that is only viewable by those invited and those with the Manage Threads permission'
        ),
    ]
    flags: Flags41 | None = None
    rate_limit_per_user: Annotated[
        float | None,
        Field(
            description='Amount of seconds a user has to wait before sending another message (0-21600);\nbots, as well as users with the permission `BYPASS_SLOWMODE`, are unaffected\n\n`rate_limit_per_user` also applies to thread creation. Users can send one message and create one thread during each `rate_limit_per_user` interval.\n\nFor thread channels, `rate_limit_per_user` is only returned if the field is set to a non-zero and non-null value.\nThe absence of this field in API calls and Gateway events should indicate that slowmode has been reset to the default value.'
        ),
    ] = None
    last_message_id: Annotated[
        str | None,
        Field(
            description='The id of the last message sent in this channel (may not point to an existing or valid message)'
        ),
    ] = None
    last_pin_timestamp: Annotated[
        str | None,
        Field(
            description='When the last pinned message was pinned.\nThis may be `null` in events such as `GUILD_CREATE` when a message is not pinned'
        ),
    ] = None
    name: Annotated[
        str, Field(description='The name of the channel (1-100 characters)')
    ]
    guild_id: Annotated[
        str | None,
        Field(
            description='The id of the guild (may be missing for some channel objects received over gateway guild dispatches)'
        ),
    ] = None
    permission_overwrites: Annotated[
        list[APIOverwrite] | None,
        Field(description='Explicit permission overwrites for members and roles'),
    ] = None
    nsfw: Annotated[bool | None, Field(description='Whether the channel is nsfw')] = (
        None
    )
    member: Annotated[
        APIThreadMember | None,
        Field(
            description='The client users member for the thread, only included in select endpoints'
        ),
    ] = None
    thread_metadata: Annotated[
        APIThreadMetadata | None,
        Field(
            description='The metadata for a thread channel not shared by other channels'
        ),
    ] = None
    message_count: Annotated[
        float | None,
        Field(
            description='Number of messages (not including the initial message or deleted messages) in a thread\n\nIf the thread was created before July 1, 2022, it stops counting at 50 messages'
        ),
    ] = None
    member_count: Annotated[
        float | None,
        Field(
            description='The approximate member count of the thread, does not count above 50 even if there are more members'
        ),
    ] = None
    owner_id: Annotated[str | None, Field(description='ID of the thread creator')] = (
        None
    )
    total_message_sent: Annotated[
        float | None,
        Field(
            description="Number of messages ever sent in a thread\n\nSimilar to `message_count` on message creation, but won't decrement when a message is deleted"
        ),
    ] = None
    applied_tags: Annotated[
        list[str] | None,
        Field(
            description='The IDs of the set of tags that have been applied to a thread in a thread-only channel'
        ),
    ] = None
    parent_id: Annotated[
        str | None, Field(description='ID of the parent channel for the thread')
    ] = None
