# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._animation_type import AnimationType
from ._api_emoji import APIEmoji


class GatewayVoiceChannelEffectSendDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: Annotated[
        str, Field(description='ID of the channel the effect was sent in')
    ]
    guild_id: Annotated[
        str, Field(description='ID of the guild the effect was sent in')
    ]
    user_id: Annotated[str, Field(description='ID of the user who sent the effect')]
    emoji: Annotated[
        APIEmoji | None,
        Field(description='The emoji sent, for emoji reaction and soundboard effects'),
    ] = None
    animation_type: Annotated[
        AnimationType | None,
        Field(
            description='The type of emoji animation, for emoji reaction and soundboard effects'
        ),
    ] = None
    animation_id: Annotated[
        float | None,
        Field(
            description='The ID of the emoji animation, for emoji reaction and soundboard effects'
        ),
    ] = None
    sound_id: Annotated[
        str | float | None,
        Field(description='The ID of the soundboard sound, for soundboard effects'),
    ] = None
    sound_volume: Annotated[
        float | None,
        Field(
            description='The volume of the soundboard sound, from 0 to 1, for soundboard effects'
        ),
    ] = None
