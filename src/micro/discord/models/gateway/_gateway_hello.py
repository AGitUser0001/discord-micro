# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_hello_data import GatewayHelloData


class GatewayHello(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[10],
        Field(
            description='Sent immediately after connecting, contains the `heartbeat_interval` to use'
        ),
    ]
    d: GatewayHelloData
    t: None
    s: None
