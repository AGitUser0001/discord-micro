# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._int53_type import Int53Type
from ._snowflake_type import SnowflakeType
from ._user_avatar_decoration_response import UserAvatarDecorationResponse
from ._user_primary_guild_response import UserPrimaryGuildResponse
from ._user_collectibles_response import UserCollectiblesResponse


class UserResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[SnowflakeType, Field(description="the user's id")]
    username: Annotated[
        str, Field(description="the user's username, not unique across the platform")
    ]
    avatar: Annotated[str | None, Field(description="the user's avatar hash")]
    discriminator: Annotated[str, Field(description="the user's Discord-tag")]
    public_flags: Annotated[
        int, Field(description="the public flags on a user's account")
    ]
    flags: Annotated[Int53Type, Field(description="the flags on a user's account")]
    bot: Annotated[
        bool | None,
        Field(description='whether the user belongs to an OAuth2 application'),
    ] = None
    system: Annotated[
        bool | None,
        Field(
            description='whether the user is an Official Discord System user (part of the urgent message system)'
        ),
    ] = None
    banner: Annotated[str | None, Field(description="the user's banner hash")] = None
    accent_color: Annotated[
        int | None,
        Field(
            description="the user's banner color encoded as an integer representation of hexadecimal color code"
        ),
    ] = None
    global_name: Annotated[
        str | None, Field(description="the user's display name, if it is set")
    ]
    avatar_decoration_data: Annotated[
        UserAvatarDecorationResponse | None,
        Field(description="data for the user's avatar decoration"),
    ] = None
    collectibles: Annotated[
        UserCollectiblesResponse | None,
        Field(description="data for the user's collectibles"),
    ] = None
    primary_guild: Annotated[
        UserPrimaryGuildResponse | None, Field(description="the user's primary guild")
    ]
