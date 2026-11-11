# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_role_colors_response import GuildRoleColorsResponse
from ._snowflake_type import SnowflakeType


class InviteGuildRoleResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    position: int
    color: int
    colors: GuildRoleColorsResponse
    icon: str | None
    unicode_emoji: str | None
    permissions: str | None = None
