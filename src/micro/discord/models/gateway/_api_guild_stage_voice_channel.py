# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_overwrite import APIOverwrite
from ._video_quality_mode import VideoQualityMode
from ._flags41 import Flags41


class APIGuildStageVoiceChannel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    type: Annotated[
        Literal[13],
        Field(description='A voice channel for hosting events with an audience'),
    ]
    flags: Flags41 | None = None
    rate_limit_per_user: Annotated[
        float | None,
        Field(
            description='Amount of seconds a user has to wait before sending another message (0-21600);\nbots, as well as users with the permission `BYPASS_SLOWMODE`, are unaffected\n\n`rate_limit_per_user` also applies to thread creation. Users can send one message and create one thread during each `rate_limit_per_user` interval.\n\nFor thread channels, `rate_limit_per_user` is only returned if the field is set to a non-zero and non-null value.\nThe absence of this field in API calls and Gateway events should indicate that slowmode has been reset to the default value.'
        ),
    ] = None
    position: Annotated[float, Field(description='Sorting position of the channel')]
    last_message_id: Annotated[
        str | None,
        Field(
            description='The id of the last message sent in this channel (may not point to an existing or valid message)'
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
    parent_id: Annotated[
        str | None,
        Field(
            description='ID of the parent category for a channel (each parent category can contain up to 50 channels)'
        ),
    ] = None
    nsfw: Annotated[bool | None, Field(description='Whether the channel is nsfw')] = (
        None
    )
    bitrate: Annotated[
        float | None,
        Field(description='The bitrate (in bits) of the voice or stage channel'),
    ] = None
    user_limit: Annotated[
        float | None, Field(description='The user limit of the voice or stage channel')
    ] = None
    rtc_region: Annotated[
        str | None,
        Field(
            description='Voice region id for the voice or stage channel, automatic when set to `null`'
        ),
    ] = None
    video_quality_mode: Annotated[
        VideoQualityMode | None,
        Field(
            description='The camera video quality mode of the voice or stage channel, `1` when not present'
        ),
    ] = None
