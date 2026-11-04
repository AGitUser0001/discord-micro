# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayMessagePollVoteDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    user_id: Annotated[str, Field(description='ID of the user')]
    channel_id: Annotated[str, Field(description='ID of the channel')]
    message_id: Annotated[str, Field(description='ID of the message')]
    guild_id: Annotated[str | None, Field(description='ID of the guild')] = None
    answer_id: Annotated[float, Field(description='ID of the answer')]
