# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayMessageDeleteBulkDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    ids: Annotated[list[str], Field(description='The ids of the messages')]
    channel_id: Annotated[str, Field(description='The id of the channel')]
    guild_id: Annotated[str | None, Field(description='The id of the guild')] = None
