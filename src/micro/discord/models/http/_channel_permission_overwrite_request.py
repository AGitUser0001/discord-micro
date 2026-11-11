# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._channel_permission_overwrites import ChannelPermissionOverwrites
from ._snowflake_type import SnowflakeType


class ChannelPermissionOverwriteRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: ChannelPermissionOverwrites | None = None
    allow: int | None = None
    deny: int | None = None
