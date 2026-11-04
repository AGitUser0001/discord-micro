# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIGuildWelcomeScreenChannel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: Annotated[str, Field(description='The channel id that is suggested')]
    description: Annotated[
        str, Field(description='The description shown for the channel')
    ]
    emoji_id: Annotated[
        str | None,
        Field(
            description='The emoji id of the emoji that is shown on the left of the channel'
        ),
    ]
    emoji_name: Annotated[
        str | None,
        Field(
            description='The emoji name of the emoji that is shown on the left of the channel'
        ),
    ]
