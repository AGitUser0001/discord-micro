# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._button_style_types import ButtonStyleTypes
from ._message_component_types import MessageComponentTypes
from ._snowflake_type import SnowflakeType
from ._component_emoji_for_request import ComponentEmojiForRequest


class ButtonComponentForMessageRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    custom_id: Annotated[str | None, Field(max_length=100, min_length=1)] = None
    style: ButtonStyleTypes
    label: Annotated[str | None, Field(max_length=80)] = None
    disabled: bool | None = None
    url: AnyUrl | None = None
    sku_id: SnowflakeType | None = None
    emoji: ComponentEmojiForRequest | None = None
