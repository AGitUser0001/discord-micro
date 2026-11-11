# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_presence_update_data import GatewayPresenceUpdateData


class GatewayUpdatePresence(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[Literal[3], Field(description="Update the client's presence")]
    d: GatewayPresenceUpdateData
