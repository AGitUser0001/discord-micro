# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags64 import Flags64
from ._api_guild_member import APIGuildMember


class GatewayThreadMemberUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str | None,
        Field(
            description='The id of the thread\n\n**This field is omitted on the member sent within each thread in the `GUILD_CREATE` event**'
        ),
    ] = None
    user_id: Annotated[
        str | None,
        Field(
            description='The id of the member\n\n**This field is omitted on the member sent within each thread in the `GUILD_CREATE` event**'
        ),
    ] = None
    join_timestamp: Annotated[
        str, Field(description='An ISO8601 timestamp for when the member last joined')
    ]
    flags: Annotated[Flags64, Field(description='Member flags combined as a bitfield')]
    member: Annotated[
        APIGuildMember | None,
        Field(
            description='Additional information about the user\n\n**This field is omitted on the member sent within each thread in the `GUILD_CREATE` event**\n\n**This field is only present when `with_member` is set to true when calling `List Thread Members` or `Get Thread Member`**'
        ),
    ] = None
    guild_id: str
