# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayWebhooksUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='The id of the guild')]
    channel_id: Annotated[str, Field(description='The id of the channel')]
