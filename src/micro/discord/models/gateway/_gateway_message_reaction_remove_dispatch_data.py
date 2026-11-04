# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type17 import Type17
from ._api_emoji import APIEmoji


class GatewayMessageReactionRemoveDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    user_id: Annotated[str, Field(description='The id of the user')]
    channel_id: Annotated[str, Field(description='The id of the channel')]
    message_id: Annotated[str, Field(description='The id of the message')]
    guild_id: Annotated[str | None, Field(description='The id of the guild')] = None
    emoji: Annotated[APIEmoji, Field(description='The emoji used to react')]
    burst: Annotated[bool, Field(description='True if this is a super-reaction')]
    type: Annotated[Type17, Field(description='The type of reaction')]
