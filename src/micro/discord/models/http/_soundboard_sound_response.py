# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse


class SoundboardSoundResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    sound_id: SnowflakeType
    volume: float
    emoji_id: SnowflakeType | None
    emoji_name: str | None
    guild_id: SnowflakeType | None = None
    available: bool
    user: UserResponse | None = None
