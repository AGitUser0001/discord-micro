# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_share_custom_user_theme_base_theme import MessageShareCustomUserThemeBaseTheme


class CustomClientThemeResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    colors: list[str]
    gradient_angle: int
    base_mix: int
    base_theme: MessageShareCustomUserThemeBaseTheme
