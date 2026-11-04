# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_guild_scheduled_event_user_add_dispatch_data import GatewayGuildScheduledEventUserAddDispatchData


class GatewayGuildScheduledEventUserAddDispatch(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    s: Annotated[
        float,
        Field(description='Sequence number, used for resuming sessions and heartbeats'),
    ]
    op: Annotated[Literal[0], Field(description='An event was dispatched')]
    t: Literal['GUILD_SCHEDULED_EVENT_USER_ADD']
    d: GatewayGuildScheduledEventUserAddDispatchData
