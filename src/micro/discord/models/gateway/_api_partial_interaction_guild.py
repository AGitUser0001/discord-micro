# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._feature import Feature
from ._locale import Locale


class APIPartialInteractionGuild(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Guild id')]
    features: Annotated[list[Feature], Field(description='Enabled guild features')]
    locale: Annotated[
        Locale,
        Field(
            description='The preferred locale of a Community guild; used in guild discovery and notices from Discord'
        ),
    ]
