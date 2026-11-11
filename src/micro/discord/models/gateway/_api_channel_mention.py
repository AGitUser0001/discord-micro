# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type8 import Type8


class APIChannelMention(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the channel')]
    guild_id: Annotated[
        str, Field(description='ID of the guild containing the channel')
    ]
    type: Annotated[Type8, Field(description='The type of channel')]
    name: Annotated[str, Field(description='The name of the channel')]
