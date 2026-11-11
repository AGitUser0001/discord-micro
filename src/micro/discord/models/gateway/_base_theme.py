# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._base_theme_enum import BaseThemeEnum


class BaseTheme(RootModel[BaseThemeEnum | None]):
    root: Annotated[
        BaseThemeEnum | None, Field(description='The mode of the theme')
    ] = None
