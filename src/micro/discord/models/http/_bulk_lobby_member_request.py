# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._flags import Flags
from ._snowflake_type import SnowflakeType


class BulkLobbyMemberRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    metadata: dict[str, Any] | None = None
    flags: Flags | None = None
    additional_name: Annotated[str | None, Field(max_length=80, min_length=1)] = None
    remove_member: bool | None = None
