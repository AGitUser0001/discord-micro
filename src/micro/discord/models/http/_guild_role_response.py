# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_role_colors_response import GuildRoleColorsResponse
from ._snowflake_type import SnowflakeType
from ._guild_role_tags_response import GuildRoleTagsResponse


class GuildRoleResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    permissions: str
    position: int
    color: int
    colors: GuildRoleColorsResponse
    hoist: bool
    managed: bool
    mentionable: bool
    icon: str | None
    unicode_emoji: str | None
    tags: GuildRoleTagsResponse | None = None
    flags: int
