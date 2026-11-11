# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayHeartbeatAck(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[11],
        Field(
            description='Sent in response to receiving a heartbeat to acknowledge that it has been received'
        ),
    ]
    t: None
    s: None
