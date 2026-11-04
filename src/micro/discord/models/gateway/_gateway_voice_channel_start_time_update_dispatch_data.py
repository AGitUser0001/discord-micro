# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayVoiceChannelStartTimeUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The channel id')]
    guild_id: Annotated[str, Field(description='The guild id')]
    voice_start_time: Annotated[
        float | None,
        Field(
            description='Unix timestamp (in seconds) of when the voice session started'
        ),
    ] = None
