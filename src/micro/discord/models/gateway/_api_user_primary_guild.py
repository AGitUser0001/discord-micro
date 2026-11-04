# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIUserPrimaryGuild(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    identity_guild_id: Annotated[
        str | None, Field(description="The id of the user's primary guild")
    ]
    identity_enabled: Annotated[
        bool | None,
        Field(
            description="Whether the user is displaying the primary guild's server tag.\nThis can be `null` if the system clears the identity, e.g. because the server no longer supports tags"
        ),
    ]
    tag: Annotated[
        str | None,
        Field(description="The text of the user's server tag. Limited to 4 characters"),
    ]
    badge: Annotated[str | None, Field(description='The server tag badge hash')]
