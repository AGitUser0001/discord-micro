# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_soundboard_sound import APISoundboardSound


class GatewayGuildSoundboardSoundsUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    soundboard_sounds: Annotated[
        list[APISoundboardSound], Field(description="The guild's soundboard sounds")
    ]
    guild_id: Annotated[str, Field(description='The id of the guild')]
