# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_identify_data import GatewayIdentifyData


class GatewayIdentify(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[2],
        Field(description='Starts a new session during the initial handshake'),
    ]
    d: GatewayIdentifyData
