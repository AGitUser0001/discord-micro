# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_message_component_emoji import APIMessageComponentEmoji


class APISelectMenuOption(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    label: Annotated[
        str, Field(description='The user-facing name of the option (max 100 chars)')
    ]
    value: Annotated[
        str, Field(description='The dev-defined value of the option (max 100 chars)')
    ]
    description: Annotated[
        str | None,
        Field(description='An additional description of the option (max 100 chars)'),
    ] = None
    emoji: Annotated[
        APIMessageComponentEmoji | None,
        Field(description='The emoji to display to the left of the option'),
    ] = None
    default: Annotated[
        bool | None,
        Field(description='Whether this option should be already-selected by default'),
    ] = None
