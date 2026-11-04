# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_emoji import APIEmoji


class GatewayMessageReactionRemoveEmojiDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    emoji: Annotated[APIEmoji, Field(description='The emoji that was removed')]
    channel_id: Annotated[str, Field(description='The id of the channel')]
    message_id: Annotated[str, Field(description='The id of the message')]
    guild_id: Annotated[str | None, Field(description='The id of the guild')] = None
