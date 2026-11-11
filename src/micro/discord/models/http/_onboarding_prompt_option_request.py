# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class OnboardingPromptOptionRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType | None = None
    title: Annotated[str, Field(max_length=50, min_length=1)]
    description: Annotated[str | None, Field(max_length=100)] = None
    emoji_id: SnowflakeType | None = None
    emoji_name: Annotated[str | None, Field(max_length=100)] = None
    emoji_animated: bool | None = None
    role_ids: Annotated[list[SnowflakeType] | None, Field(max_length=50)] = None
    channel_ids: Annotated[list[SnowflakeType] | None, Field(max_length=50)] = None
