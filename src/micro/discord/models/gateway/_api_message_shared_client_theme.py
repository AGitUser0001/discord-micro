# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._base_theme import BaseTheme


class APIMessageSharedClientTheme(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    colors: Annotated[
        list[str],
        Field(description='The hexadecimal-encoded colors of the theme (max of 5)'),
    ]
    gradient_angle: Annotated[
        float, Field(description="The direction of the theme's colors (max of 360)")
    ]
    base_mix: Annotated[
        float, Field(description="The intensity of the theme's colors (max of 100)")
    ]
    base_theme: Annotated[
        BaseTheme | None, Field(description='The mode of the theme')
    ] = None
