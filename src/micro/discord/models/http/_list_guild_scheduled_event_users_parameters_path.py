# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class ListGuildScheduledEventUsersParametersPath(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: SnowflakeType
    guild_scheduled_event_id: SnowflakeType
