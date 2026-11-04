# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._text_input_style_types import TextInputStyleTypes


class TextInputComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    custom_id: str
    style: TextInputStyleTypes
    label: str | None
    value: str | None = None
    placeholder: str | None = None
    required: bool | None = None
    min_length: int | None
    max_length: int | None
