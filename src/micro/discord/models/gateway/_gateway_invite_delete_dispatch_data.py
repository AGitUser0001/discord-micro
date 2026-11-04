# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayInviteDeleteDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: Annotated[str, Field(description='The channel of the invite')]
    guild_id: Annotated[str | None, Field(description='The guild of the invite')] = None
    code: Annotated[str, Field(description='The unique invite code')]
