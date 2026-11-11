# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayRequestChannelInfoData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[
        str, Field(description='The guild id to request channel info for')
    ]
    fields: Annotated[
        list[str],
        Field(
            description='The fields to request. The current available fields are `status` and `voice_start_time`'
        ),
    ]
