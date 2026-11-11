# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type11 import Type11


class APIMessageReference(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Type11 | None, Field(description='Type of reference')] = None
    message_id: Annotated[
        str | None, Field(description='ID of the originating message')
    ] = None
    channel_id: Annotated[
        str, Field(description="ID of the originating message's channel")
    ]
    guild_id: Annotated[
        str | None, Field(description="ID of the originating message's guild")
    ] = None
