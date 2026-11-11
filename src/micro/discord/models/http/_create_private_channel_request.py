# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._access_token import AccessToken
from ._snowflake_type import SnowflakeType


class CreatePrivateChannelRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    recipient_id: SnowflakeType | None = None
    access_tokens: Annotated[list[AccessToken] | None, Field(max_length=1521)] = None
    nicks: dict[str, Any] | None = None
