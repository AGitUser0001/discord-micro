# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags7 import Flags7
from ._premium_type import PremiumType
from ._public_flags import PublicFlags
from ._api_avatar_decoration_data import APIAvatarDecorationData
from ._api_user_primary_guild import APIUserPrimaryGuild
from ._api_collectibles import APICollectibles


class APIUser(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description="The user's id")]
    username: Annotated[
        str, Field(description="The user's username, not unique across the platform")
    ]
    discriminator: Annotated[str, Field(description="The user's Discord-tag")]
    global_name: Annotated[
        str | None, Field(description="The user's display name, if it is set")
    ]
    avatar: Annotated[str | None, Field(description="The user's avatar hash")]
    bot: Annotated[
        bool | None,
        Field(description='Whether the user belongs to an OAuth2 application'),
    ] = None
    system: Annotated[
        bool | None,
        Field(
            description='Whether the user is an Official Discord System user (part of the urgent message system)'
        ),
    ] = None
    mfa_enabled: Annotated[
        bool | None,
        Field(description='Whether the user has two factor enabled on their account'),
    ] = None
    banner: Annotated[str | None, Field(description="The user's banner hash")] = None
    accent_color: Annotated[
        float | None,
        Field(
            description="The user's banner color encoded as an integer representation of hexadecimal color code"
        ),
    ] = None
    locale: Annotated[
        str | None, Field(description="The user's chosen language option")
    ] = None
    verified: Annotated[
        bool | None,
        Field(description='Whether the email on this account has been verified'),
    ] = None
    email: Annotated[str | None, Field(description="The user's email")] = None
    flags: Annotated[
        Flags7 | None, Field(description="The flags on a user's account")
    ] = None
    premium_type: Annotated[
        PremiumType | None,
        Field(description="The type of Nitro subscription on a user's account"),
    ] = None
    public_flags: Annotated[
        PublicFlags | None, Field(description="The public flags on a user's account")
    ] = None
    avatar_decoration: Annotated[
        str | None,
        Field(deprecated=True, description="The user's avatar decoration hash"),
    ] = None
    avatar_decoration_data: Annotated[
        APIAvatarDecorationData | None,
        Field(description="The data for the user's avatar decoration"),
    ] = None
    collectibles: Annotated[
        APICollectibles | None,
        Field(description="The data for the user's collectibles"),
    ] = None
    primary_guild: Annotated[
        APIUserPrimaryGuild | None, Field(description="The user's primary guild")
    ] = None
