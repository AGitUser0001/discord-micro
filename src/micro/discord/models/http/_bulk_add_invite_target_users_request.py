# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class BulkAddInviteTargetUsersRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    user_ids: Annotated[
        list[SnowflakeType],
        Field(
            description='The IDs of the users to target.', max_length=1000, min_length=1
        ),
    ]
