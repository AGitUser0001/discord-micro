# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayRequestGuildMembersDataWithQuery(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='ID of the guild to get members for')]
    presences: Annotated[
        bool | None,
        Field(
            description='Used to specify if we want the presences of the matched members'
        ),
    ] = None
    nonce: Annotated[
        str | None,
        Field(
            description='Nonce to identify the Guild Members Chunk response\n\nNonce can only be up to 32 bytes. If you send an invalid nonce it will be ignored and the reply member_chunk(s) will not have a `nonce` set.'
        ),
    ] = None
    query: Annotated[
        str,
        Field(
            description='String that username starts with, or an empty string to return all members'
        ),
    ]
    limit: Annotated[
        float,
        Field(
            description='Maximum number of members to send matching the `query`;\na limit of `0` can be used with an empty string `query` to return all members'
        ),
    ]
