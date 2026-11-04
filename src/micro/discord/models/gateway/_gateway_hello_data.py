# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayHelloData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    heartbeat_interval: Annotated[
        float,
        Field(
            description='The interval (in milliseconds) the client should heartbeat with'
        ),
    ]
