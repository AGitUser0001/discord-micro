# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class ListMyGuildsParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    before: SnowflakeType | None = None
    after: SnowflakeType | None = None
    limit: Annotated[int | None, Field(ge=1, le=200)] = None
    shard: Annotated[int | None, Field(ge=0)] = None
    with_counts: bool | None = None
