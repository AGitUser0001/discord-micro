# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_identify_properties import GatewayIdentifyProperties
from ._gateway_presence_update_data import GatewayPresenceUpdateData


class GatewayIdentifyData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    token: Annotated[str, Field(description='Authentication token')]
    properties: Annotated[
        GatewayIdentifyProperties, Field(description='Connection properties')
    ]
    compress: Annotated[
        bool | None,
        Field(description='Whether this connection supports compression of packets'),
    ] = None
    large_threshold: Annotated[
        float | None,
        Field(
            description='Value between 50 and 250, total number of members where the gateway will stop sending\noffline members in the guild member list'
        ),
    ] = None
    shard: Annotated[
        list[float] | None,
        Field(description='Used for Guild Sharding', max_length=2, min_length=2),
    ] = None
    presence: Annotated[
        GatewayPresenceUpdateData | None,
        Field(description='Presence structure for initial presence information'),
    ] = None
    intents: Annotated[
        float, Field(description='The Gateway Intents you wish to receive')
    ]
