# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_features import GuildFeatures
from ._snowflake_type import SnowflakeType


class MyGuildResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    icon: str | None
    banner: str | None
    owner: bool
    permissions: str
    features: list[GuildFeatures]
    approximate_member_count: int | None = None
    approximate_presence_count: int | None = None
