# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class GuildTemplateChannelTags(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: int | None
    name: str
    emoji_id: SnowflakeType | None
    emoji_name: str | None
    moderated: bool | None
