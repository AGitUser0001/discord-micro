# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class BulkUpdateGuildChannelsRequestItem(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType | None = None
    position: Annotated[int | None, Field(ge=0)] = None
    parent_id: SnowflakeType | None = None
    lock_permissions: bool | None = None
