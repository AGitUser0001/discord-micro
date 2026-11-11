# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ProvisionalTokenResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    token_type: str
    access_token: str
    expires_in: int
    scope: str
    id_token: str
    refresh_token: str | None = None
    scopes: list[str] | None = None
    expires_at_s: int | None = None
