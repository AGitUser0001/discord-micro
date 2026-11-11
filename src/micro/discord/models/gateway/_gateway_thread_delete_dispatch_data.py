# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type20 import Type20


class GatewayThreadDeleteDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    guild_id: Annotated[str, Field(description='The id of the guild')]
    parent_id: Annotated[
        str, Field(description='The id of the parent channel of the thread')
    ]
    type: Annotated[Type20, Field(description='The type of the channel')]
