# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIRoleColors(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    primary_color: Annotated[float, Field(description='The primary color for the role')]
    secondary_color: Annotated[
        float | None,
        Field(
            description='The secondary color for the role, this will make the role a gradient between the other provided colors'
        ),
    ]
    tertiary_color: Annotated[
        float | None,
        Field(
            description='The tertiary color for the role, this will turn the gradient into a holographic style'
        ),
    ]
