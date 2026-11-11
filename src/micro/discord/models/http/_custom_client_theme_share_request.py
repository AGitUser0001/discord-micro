# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._color import Color
from ._message_share_custom_user_theme_base_theme import MessageShareCustomUserThemeBaseTheme


class CustomClientThemeShareRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    colors: Annotated[list[Color], Field(max_length=5, min_length=1)]
    gradient_angle: Annotated[int, Field(ge=0, le=360)]
    base_mix: Annotated[int, Field(ge=0, le=100)]
    base_theme: MessageShareCustomUserThemeBaseTheme | None = None
