# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class UpdateGuildMemberRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    nick: Annotated[str | None, Field(max_length=32)] = None
    roles: Annotated[list[SnowflakeType | None] | None, Field(max_length=350)] = None
    mute: bool | None = None
    deaf: bool | None = None
    channel_id: SnowflakeType | None = None
    communication_disabled_until: AwareDatetime | None = None
    flags: int | None = None
