# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class ListMessagesParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    around: SnowflakeType | None = None
    before: SnowflakeType | None = None
    after: SnowflakeType | None = None
    limit: Annotated[int | None, Field(ge=1, le=100)] = None
