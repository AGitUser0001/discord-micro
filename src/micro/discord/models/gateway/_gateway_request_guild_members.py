# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_request_guild_members_data import GatewayRequestGuildMembersData


class GatewayRequestGuildMembers(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[8],
        Field(
            description='Request information about offline guild members in a large guild'
        ),
    ]
    d: GatewayRequestGuildMembersData
