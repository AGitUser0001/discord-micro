# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_guild_member import APIGuildMember


class GatewayTypingStartDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: Annotated[str, Field(description='The id of the channel')]
    guild_id: Annotated[str | None, Field(description='The id of the guild')] = None
    user_id: Annotated[str, Field(description='The id of the user')]
    timestamp: Annotated[
        float,
        Field(description='Unix time (in seconds) of when the user started typing'),
    ]
    member: Annotated[
        APIGuildMember | None,
        Field(description='The member who started typing if this happened in a guild'),
    ] = None
