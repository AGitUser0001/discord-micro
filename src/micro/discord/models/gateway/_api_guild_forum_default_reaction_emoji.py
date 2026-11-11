# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIGuildForumDefaultReactionEmoji(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    emoji_id: Annotated[
        str | None, Field(description="The id of a guild's custom emoji")
    ]
    emoji_name: Annotated[
        str | None, Field(description='The unicode character of the emoji')
    ]
