# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_guild_welcome_screen_channel import APIGuildWelcomeScreenChannel


class APIGuildWelcomeScreen(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    description: Annotated[
        str | None, Field(description='The welcome screen short message')
    ]
    welcome_channels: Annotated[
        list[APIGuildWelcomeScreenChannel],
        Field(description='Array of suggested channels'),
    ]
