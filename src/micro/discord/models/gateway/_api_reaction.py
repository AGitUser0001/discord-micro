# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_reaction_count_details import APIReactionCountDetails
from ._api_partial_emoji import APIPartialEmoji


class APIReaction(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    count: Annotated[
        float,
        Field(
            description='Total number of times this emoji has been used to react (including super reacts)'
        ),
    ]
    count_details: Annotated[
        APIReactionCountDetails,
        Field(
            description='An object detailing the individual reaction counts for different types of reactions'
        ),
    ]
    me: Annotated[
        bool, Field(description='Whether the current user reacted using this emoji')
    ]
    me_burst: Annotated[
        bool,
        Field(description='Whether the current user super-reacted using this emoji'),
    ]
    emoji: Annotated[APIPartialEmoji, Field(description='Emoji information')]
    burst_colors: Annotated[
        list[str], Field(description='Hexadecimal colors used for this super reaction')
    ]
