# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_request_soundboard_sounds_data import GatewayRequestSoundboardSoundsData


class GatewayRequestSoundboardSounds(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[31],
        Field(
            description='Request information about soundboard sounds in a set of guilds'
        ),
    ]
    d: GatewayRequestSoundboardSoundsData
