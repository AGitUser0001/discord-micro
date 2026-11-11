# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_partial_emoji import APIPartialEmoji


class APIPollMedia(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    text: Annotated[
        str | None,
        Field(
            description='The text of the field\n\nThe maximum length is `300` for the question, and `55` for any answer'
        ),
    ] = None
    emoji: Annotated[
        APIPartialEmoji | None, Field(description='The emoji of the field')
    ] = None
