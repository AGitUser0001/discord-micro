# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class MessageShareCustomUserThemeBaseTheme(IntEnum):
    UNSET = 0
    DARK = 1
    LIGHT = 2
    DARKER = 3
    MIDNIGHT = 4
