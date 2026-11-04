# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class OAuth2GetOpenIDConnectUserInfoResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sub: str
    email: str | None = None
    email_verified: bool | None = None
    preferred_username: str | None = None
    nickname: str | None = None
    picture: str | None = None
    locale: str | None = None
