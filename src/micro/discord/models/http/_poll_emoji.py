# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class PollEmoji(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        SnowflakeType | None, Field(description='The ID of the custom emoji')
    ] = None
    name: Annotated[
        str | None,
        Field(
            description='The name of the emoji, or the unicode emoji character',
            max_length=32,
        ),
    ] = None
    animated: Annotated[
        bool | None, Field(description='Whether the emoji is animated')
    ] = None
