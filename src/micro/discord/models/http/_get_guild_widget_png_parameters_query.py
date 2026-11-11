# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._widget_image_styles import WidgetImageStyles


class GetGuildWidgetPngParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    style: WidgetImageStyles | None = None
