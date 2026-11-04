# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_user import APIUser


class APISoundboardSound(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(description='The name of this sound')]
    sound_id: Annotated[str, Field(description='The id of this sound')]
    volume: Annotated[float, Field(description='The volume of this sound, from 0 to 1')]
    emoji_id: Annotated[
        str | None, Field(description="The id of this sound's custom emoji")
    ]
    emoji_name: Annotated[
        str | None,
        Field(description="The unicode character of this sound's standard emoji"),
    ]
    guild_id: Annotated[
        str | None, Field(description='The id of the guild that this sound is in')
    ] = None
    available: Annotated[
        bool,
        Field(
            description='Whether this sound can be used (for guild sounds), may be false due to loss of Server Boosts'
        ),
    ]
    user: Annotated[
        APIUser | None, Field(description='The user who created this sound')
    ] = None
