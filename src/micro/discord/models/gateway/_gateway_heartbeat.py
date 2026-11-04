# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_heartbeat_data import GatewayHeartbeatData


class GatewayHeartbeat(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[1],
        Field(
            description='A bidirectional opcode to maintain an active gateway connection.\nFired periodically by the client, or fired by the gateway to request an immediate heartbeat from the client.'
        ),
    ]
    d: GatewayHeartbeatData | None
