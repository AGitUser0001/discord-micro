# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_select_default_value_types import SnowflakeSelectDefaultValueTypes
from ._snowflake_type import SnowflakeType


class RoleSelectDefaultValueResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: SnowflakeSelectDefaultValueTypes
    id: SnowflakeType
