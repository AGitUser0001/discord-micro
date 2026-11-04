# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._allowed_mention_types import AllowedMentionTypes
from ._snowflake_type import SnowflakeType


class MessageAllowedMentionsRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    parse: Annotated[
        list[AllowedMentionTypes | None] | None, Field(max_length=1521)
    ] = None
    users: Annotated[list[SnowflakeType | None] | None, Field(max_length=100)] = None
    roles: Annotated[list[SnowflakeType | None] | None, Field(max_length=100)] = None
    replied_user: bool | None = None
