# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class UpdateSelfVoiceStateRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    request_to_speak_timestamp: AwareDatetime | None = None
    suppress: bool | None = None
    channel_id: SnowflakeType | None = None
