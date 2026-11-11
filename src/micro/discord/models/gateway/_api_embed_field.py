# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIEmbedField(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[
        str, Field(description='Name of the field\n\nLength limit: 256 characters')
    ]
    value: Annotated[
        str, Field(description='Value of the field\n\nLength limit: 1024 characters')
    ]
    inline: Annotated[
        bool | None,
        Field(description='Whether or not this field should display inline'),
    ] = None
