# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class BotPartnerSdkTokenRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    provisional_user_id: SnowflakeType | None = None
    external_user_id: Annotated[str, Field(max_length=1024, min_length=1)]
    preferred_global_name: Annotated[str | None, Field(max_length=32, min_length=1)] = (
        None
    )
