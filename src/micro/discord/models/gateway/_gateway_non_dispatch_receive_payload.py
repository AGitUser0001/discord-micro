# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_heartbeat_ack import GatewayHeartbeatAck
from ._gateway_heartbeat_request import GatewayHeartbeatRequest
from ._gateway_invalid_session import GatewayInvalidSession
from ._gateway_reconnect import GatewayReconnect
from ._gateway_hello import GatewayHello


class GatewayNonDispatchReceivePayload(
    RootModel[
        GatewayHeartbeatAck
        | GatewayHeartbeatRequest
        | GatewayHello
        | GatewayInvalidSession
        | GatewayReconnect
    ]
):
    root: Annotated[
        GatewayHeartbeatAck
        | GatewayHeartbeatRequest
        | GatewayHello
        | GatewayInvalidSession
        | GatewayReconnect,
        Field(discriminator='op'),
    ]
