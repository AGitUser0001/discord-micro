# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class UserPrimaryGuildResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    identity_guild_id: Annotated[
        SnowflakeType | None, Field(description="the id of the user's primary guild")
    ]
    identity_enabled: Annotated[
        bool | None,
        Field(
            description="whether the user is displaying the primary guild's server tag"
        ),
    ]
    tag: Annotated[
        str | None,
        Field(description="the text of the user's server tag, limited to 4 characters"),
    ]
    badge: Annotated[str | None, Field(description='the server tag badge hash')]
