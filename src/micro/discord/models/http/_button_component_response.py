# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._button_style_types import ButtonStyleTypes
from ._message_component_types import MessageComponentTypes
from ._snowflake_type import SnowflakeType
from ._component_emoji_response import ComponentEmojiResponse


class ButtonComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    custom_id: str | None = None
    style: ButtonStyleTypes
    label: str | None = None
    disabled: bool | None = None
    emoji: ComponentEmojiResponse | None = None
    url: AnyUrl | None = None
    sku_id: SnowflakeType | None = None
