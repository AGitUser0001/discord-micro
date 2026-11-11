# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._target_type import TargetType
from ._api_user import APIUser
from ._partial_api_application import PartialAPIApplication


class GatewayInviteCreateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: Annotated[str, Field(description='The channel the invite is for')]
    code: Annotated[str, Field(description='The unique invite code')]
    created_at: Annotated[
        str, Field(description='The time at which the invite was created')
    ]
    guild_id: Annotated[str | None, Field(description='The guild of the invite')] = None
    inviter: Annotated[
        APIUser | None, Field(description='The user that created the invite')
    ] = None
    max_age: Annotated[
        float, Field(description='How long the invite is valid for (in seconds)')
    ]
    max_uses: Annotated[
        float, Field(description='The maximum number of times the invite can be used')
    ]
    target_type: Annotated[
        TargetType | None,
        Field(description='The type of target for this voice channel invite'),
    ] = None
    target_user: Annotated[
        APIUser | None,
        Field(
            description='The user whose stream to display for this voice channel stream invite'
        ),
    ] = None
    target_application: Annotated[
        PartialAPIApplication | None,
        Field(
            description='The embedded application to open for this voice channel embedded application invite'
        ),
    ] = None
    temporary: Annotated[
        bool,
        Field(
            description="Whether or not the invite is temporary (invited users will be kicked on disconnect unless they're assigned a role)"
        ),
    ]
    uses: Annotated[
        Literal[0],
        Field(
            description='How many times the invite has been used (always will be `0`)'
        ),
    ]
    expires_at: Annotated[
        str | None, Field(description='The expiration date of this invite.')
    ]
    role_ids: Annotated[
        list[str] | None,
        Field(
            description='The role ID(s) for roles in the guild given to the users that accept this invite'
        ),
    ] = None
