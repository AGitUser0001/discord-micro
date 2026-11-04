# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._user_avatar_decoration_response import UserAvatarDecorationResponse
from ._user_collectibles_response import UserCollectiblesResponse
from ._user_response import UserResponse


class GuildMemberResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    avatar: Annotated[str | None, Field(description="the member's guild avatar hash")]
    avatar_decoration_data: Annotated[
        UserAvatarDecorationResponse | None,
        Field(description="data for the member's guild avatar decoration"),
    ] = None
    banner: Annotated[str | None, Field(description="the member's guild banner hash")]
    communication_disabled_until: Annotated[
        AwareDatetime | None,
        Field(
            description="when the user's timeout will expire and the user will be able to communicate in the guild again, null or a time in the past if the user is not timed out"
        ),
    ]
    flags: Annotated[
        int,
        Field(description='guild member flags represented as a bit set, defaults to 0'),
    ]
    joined_at: Annotated[
        AwareDatetime, Field(description='when the user joined the guild')
    ]
    nick: Annotated[str | None, Field(description="this user's guild nickname")]
    pending: Annotated[
        bool,
        Field(
            description="whether the user has not yet passed the guild's Membership Screening requirements"
        ),
    ]
    premium_since: Annotated[
        AwareDatetime | None,
        Field(description='when the user started boosting the guild'),
    ]
    roles: Annotated[list[SnowflakeType], Field(description='array of role object ids')]
    collectibles: Annotated[
        UserCollectiblesResponse | None,
        Field(description="data for the member's collectibles"),
    ] = None
    user: Annotated[
        UserResponse, Field(description='the user this guild member represents')
    ]
    mute: Annotated[
        bool, Field(description='whether the user is muted in voice channels')
    ]
    deaf: Annotated[
        bool, Field(description='whether the user is deafened in voice channels')
    ]
