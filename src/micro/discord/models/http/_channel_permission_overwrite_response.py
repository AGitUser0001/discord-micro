# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._channel_permission_overwrites import ChannelPermissionOverwrites
from ._snowflake_type import SnowflakeType


class ChannelPermissionOverwriteResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: ChannelPermissionOverwrites
    allow: str
    deny: str
