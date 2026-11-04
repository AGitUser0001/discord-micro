# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class UpdateThreadTagRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(max_length=50, min_length=0)]
    emoji_id: SnowflakeType | None = None
    emoji_name: Annotated[str | None, Field(max_length=100)] = None
    moderated: bool | None = None
    id: SnowflakeType | None = None
