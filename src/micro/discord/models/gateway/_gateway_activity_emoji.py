# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayActivityEmoji(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str | None, Field(description='Emoji id')] = None
    name: Annotated[
        str | None,
        Field(description='Emoji name (can be null only in reaction emoji objects)'),
    ]
    animated: Annotated[
        bool | None, Field(description='Whether this emoji is animated')
    ] = None
