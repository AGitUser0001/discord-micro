# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_overwrite import APIOverwrite
from ._default_auto_archive_duration import DefaultAutoArchiveDuration
from ._flags24 import Flags24


class PartialAPINewsChannelPickAPIChannelidtype(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    type: Annotated[
        Literal[5],
        Field(
            description='A channel that users can follow and crosspost into their own guild'
        ),
    ]
    flags: Flags24 | None = None
    rate_limit_per_user: Annotated[
        float | None,
        Field(
            description='Amount of seconds a user has to wait before sending another message (0-21600);\nbots, as well as users with the permission `BYPASS_SLOWMODE`, are unaffected\n\n`rate_limit_per_user` also applies to thread creation. Users can send one message and create one thread during each `rate_limit_per_user` interval.\n\nFor thread channels, `rate_limit_per_user` is only returned if the field is set to a non-zero and non-null value.\nThe absence of this field in API calls and Gateway events should indicate that slowmode has been reset to the default value.'
        ),
    ] = None
    position: Annotated[
        float | None, Field(description='Sorting position of the channel')
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
        str | None, Field(description='The name of the channel (1-100 characters)')
    ] = None
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
    parent_id: Annotated[
        str | None,
        Field(
            description='ID of the parent category for a channel (each parent category can contain up to 50 channels)'
        ),
    ] = None
    nsfw: Annotated[bool | None, Field(description='Whether the channel is nsfw')] = (
        None
    )
    default_auto_archive_duration: Annotated[
        DefaultAutoArchiveDuration | None,
        Field(
            description='Default duration for newly created threads, in minutes, to automatically archive the thread after recent activity'
        ),
    ] = None
    default_thread_rate_limit_per_user: Annotated[
        float | None,
        Field(
            description='The initial `rate_limit_per_user` to set on newly created threads.\nThis field is copied to the thread at creation time and does not live update'
        ),
    ] = None
    topic: Annotated[
        str | None, Field(description='The channel topic (0-1024 characters)')
    ] = None
