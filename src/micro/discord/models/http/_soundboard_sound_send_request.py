# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class SoundboardSoundSendRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sound_id: SnowflakeType
    source_guild_id: SnowflakeType | None = None
