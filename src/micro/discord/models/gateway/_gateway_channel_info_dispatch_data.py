# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_channel_info_channel import GatewayChannelInfoChannel


class GatewayChannelInfoDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='The guild id')]
    channels: Annotated[
        list[GatewayChannelInfoChannel],
        Field(description='Ephemeral data for channels in the guild'),
    ]
