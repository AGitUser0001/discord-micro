# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayChannelPinsUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str | None, Field(description='The id of the guild')] = None
    channel_id: Annotated[str, Field(description='The id of the channel')]
    last_pin_timestamp: Annotated[
        str | None,
        Field(
            description='The time at which the most recent pinned message was pinned'
        ),
    ] = None
