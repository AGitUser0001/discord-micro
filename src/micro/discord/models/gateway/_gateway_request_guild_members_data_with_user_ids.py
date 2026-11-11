# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayRequestGuildMembersDataWithUserIds(BaseModel):
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
    user_ids: Annotated[
        str | list[str],
        Field(description='Used to specify which users you wish to fetch'),
    ]
