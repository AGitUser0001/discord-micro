# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._verification_level import VerificationLevel
from ._feature import Feature
from ._api_guild_welcome_screen import APIGuildWelcomeScreen


class APIPartialGuild(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Guild id')]
    name: Annotated[
        str,
        Field(
            description='Guild name (2-100 characters, excluding trailing and leading whitespace)'
        ),
    ]
    icon: Annotated[str | None, Field(description='Icon hash')]
    splash: Annotated[str | None, Field(description='Splash hash')]
    banner: Annotated[str | None, Field(description='Banner hash')] = None
    description: Annotated[
        str | None, Field(description='The description for the guild')
    ] = None
    features: Annotated[
        list[Feature] | None, Field(description='Enabled guild features')
    ] = None
    verification_level: Annotated[
        VerificationLevel | None,
        Field(description='Verification level required for the guild'),
    ] = None
    vanity_url_code: Annotated[
        str | None, Field(description='The vanity url code for the guild')
    ] = None
    welcome_screen: Annotated[
        APIGuildWelcomeScreen | None,
        Field(
            description='The welcome screen of a Community guild, shown to new members\n\nReturned in the invite object'
        ),
    ] = None
