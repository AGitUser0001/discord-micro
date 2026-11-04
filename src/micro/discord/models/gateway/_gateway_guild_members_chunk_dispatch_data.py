# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_guild_members_chunk_presence import GatewayGuildMembersChunkPresence
from ._api_guild_member import APIGuildMember


class GatewayGuildMembersChunkDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='The id of the guild')]
    members: Annotated[list[APIGuildMember], Field(description='Set of guild members')]
    chunk_index: Annotated[
        float,
        Field(
            description='The chunk index in the expected chunks for this response (`0 <= chunk_index < chunk_count`)'
        ),
    ]
    chunk_count: Annotated[
        float,
        Field(description='The total number of expected chunks for this response'),
    ]
    not_found: Annotated[
        list[Any] | None,
        Field(
            description='If passing an invalid id to `REQUEST_GUILD_MEMBERS`, it will be returned here'
        ),
    ] = None
    presences: Annotated[
        list[GatewayGuildMembersChunkPresence] | None,
        Field(
            description='If passing true to `REQUEST_GUILD_MEMBERS`, presences of the returned members will be here'
        ),
    ] = None
    nonce: Annotated[
        str | None, Field(description='The nonce used in the Guild Members Request')
    ] = None
