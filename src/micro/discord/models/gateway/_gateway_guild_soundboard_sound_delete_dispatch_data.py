# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayGuildSoundboardSoundDeleteDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sound_id: Annotated[str, Field(description='The id of the sound that was deleted')]
    guild_id: Annotated[str, Field(description='The id of the guild the sound was in')]
