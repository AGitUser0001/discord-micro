# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class SoundboardCreateRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(max_length=32, min_length=2)]
    volume: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    emoji_id: SnowflakeType | None = None
    emoji_name: Annotated[str | None, Field(max_length=32, min_length=1)] = None
    sound: Annotated[str, Field(json_schema_extra={'contentEncoding': 'base64'})]
