# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._status6 import Status6
from ._gateway_activity_update_data import GatewayActivityUpdateData


class GatewayPresenceUpdateData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    since: Annotated[
        float | None,
        Field(
            description='Unix time (in milliseconds) of when the client went idle, or `null` if the client is not idle'
        ),
    ]
    activities: Annotated[
        list[GatewayActivityUpdateData], Field(description="The user's activities")
    ]
    status: Annotated[Status6, Field(description="The user's new status")]
    afk: Annotated[bool, Field(description='Whether or not the client is afk')]
