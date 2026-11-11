# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class GuildRoleColorsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    primary_color: int
    secondary_color: int | None
    tertiary_color: int | None
