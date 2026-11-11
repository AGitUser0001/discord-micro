# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class MessageAttachmentRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    filename: Annotated[str | None, Field(max_length=1024, min_length=1)] = None
    description: Annotated[str | None, Field(max_length=1024)] = None
    duration_secs: Annotated[float | None, Field(ge=0.0, le=2147483647.0)] = None
    waveform: Annotated[str | None, Field(max_length=400)] = None
    title: Annotated[str | None, Field(max_length=1024)] = None
    is_spoiler: bool | None = None
