# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIGuildForumTag(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the tag')]
    name: Annotated[str, Field(description='The name of the tag (0-20 characters)')]
    moderated: Annotated[
        bool,
        Field(
            description='Whether this tag can only be added to or removed from threads by a member with the `MANAGE_THREADS` permission'
        ),
    ]
    emoji_id: Annotated[
        str | None, Field(description="The id of a guild's custom emoji")
    ]
    emoji_name: Annotated[
        str | None, Field(description='The unicode character of the emoji')
    ]
