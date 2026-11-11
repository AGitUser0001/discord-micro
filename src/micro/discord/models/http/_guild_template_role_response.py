# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_template_role_colors_response import GuildTemplateRoleColorsResponse


class GuildTemplateRoleResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: int
    name: str
    permissions: str
    color: int
    colors: GuildTemplateRoleColorsResponse | None
    hoist: bool
    mentionable: bool
    icon: str | None
    unicode_emoji: str | None
