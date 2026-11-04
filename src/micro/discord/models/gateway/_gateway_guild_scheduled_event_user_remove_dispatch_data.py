# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayGuildScheduledEventUserRemoveDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_scheduled_event_id: str
    user_id: str
    guild_id: str
