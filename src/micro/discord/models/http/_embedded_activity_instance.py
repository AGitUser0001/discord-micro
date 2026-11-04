# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._guild_channel_location import GuildChannelLocation
from ._private_channel_location import PrivateChannelLocation


class EmbeddedActivityInstance(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    application_id: SnowflakeType
    instance_id: str
    launch_id: str
    location: GuildChannelLocation | PrivateChannelLocation
    users: list[SnowflakeType]
