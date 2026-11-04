# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayRequestGuildMemberRateLimitMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[
        str, Field(description='Id of the guild members were requested for')
    ]
    nonce: Annotated[
        str | None,
        Field(
            description='Nonce used to identify the GatewayGuildMembersChunkDispatch response'
        ),
    ] = None
