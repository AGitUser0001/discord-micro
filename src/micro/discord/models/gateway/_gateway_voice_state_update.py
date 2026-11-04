# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_voice_state_update_data import GatewayVoiceStateUpdateData


class GatewayVoiceStateUpdate(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[4],
        Field(description='Used to join/leave or move between voice channels'),
    ]
    d: GatewayVoiceStateUpdateData
