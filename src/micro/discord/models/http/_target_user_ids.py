# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class TargetUserIds(RootModel[list[SnowflakeType]]):
    root: Annotated[
        list[SnowflakeType],
        Field(
            description='The IDs of the users to target with this invite.',
            max_length=1000,
        ),
    ]
