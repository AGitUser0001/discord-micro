# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_request_channel_info_data import GatewayRequestChannelInfoData


class GatewayRequestChannelInfo(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[43],
        Field(description='Request ephemeral channel data for channels in a guild.'),
    ]
    d: GatewayRequestChannelInfoData
