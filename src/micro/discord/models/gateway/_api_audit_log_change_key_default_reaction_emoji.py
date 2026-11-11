# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_guild_forum_default_reaction_emoji import APIGuildForumDefaultReactionEmoji


class APIAuditLogChangeKeyDefaultReactionEmoji(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['default_reaction_emoji']
    new_value: Annotated[
        APIGuildForumDefaultReactionEmoji | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: APIGuildForumDefaultReactionEmoji | None = None
