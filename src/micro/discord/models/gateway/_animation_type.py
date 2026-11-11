# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._animation_type_enum import AnimationTypeEnum


class AnimationType(RootModel[AnimationTypeEnum | None]):
    root: Annotated[
        AnimationTypeEnum | None,
        Field(
            description='The type of emoji animation, for emoji reaction and soundboard effects'
        ),
    ] = None
