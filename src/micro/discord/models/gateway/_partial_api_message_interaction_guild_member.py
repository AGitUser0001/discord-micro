# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class PartialAPIMessageInteractionGuildMember(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    nick: Annotated[str | None, Field(description='This users guild nickname')] = None
    roles: Annotated[list[str], Field(description='Array of role object ids')]
    premium_since: Annotated[
        str | None, Field(description='When the user started boosting the guild')
    ] = None
    pending: Annotated[
        bool | None,
        Field(
            description="Whether the user has not yet passed the guild's Membership Screening requirements"
        ),
    ] = None
    communication_disabled_until: Annotated[
        str | None,
        Field(
            description='Timestamp of when the time out will be removed; until then, they cannot interact with the guild'
        ),
    ] = None
    joined_at: Annotated[
        str | None, Field(description='When the user joined the guild')
    ]
    avatar: Annotated[
        str | None, Field(description="The member's guild avatar hash")
    ] = None
    deaf: Annotated[
        bool, Field(description='Whether the user is deafened in voice channels')
    ]
    mute: Annotated[
        bool, Field(description='Whether the user is muted in voice channels')
    ]
