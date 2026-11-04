# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_request_guild_member_rate_limit_metadata import GatewayRequestGuildMemberRateLimitMetadata


class GatewayRateLimitedDispatchDataRequestGuildMembers(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    opcode: Annotated[
        Literal[8],
        Field(description='Gateway opcode of the event that was rate limited'),
    ]
    retry_after: Annotated[
        float,
        Field(
            description='The number of seconds to wait before submitting another request'
        ),
    ]
    meta: Annotated[
        GatewayRequestGuildMemberRateLimitMetadata,
        Field(description='Metadata for the event that was rate limited'),
    ]
