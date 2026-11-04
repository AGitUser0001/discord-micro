# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._text_input_style_types import TextInputStyleTypes


class TextInputComponentForModalRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    custom_id: Annotated[str, Field(max_length=100, min_length=1)]
    style: TextInputStyleTypes
    label: Annotated[str | None, Field(max_length=45, min_length=1)] = None
    value: Annotated[str | None, Field(max_length=4000)] = None
    placeholder: Annotated[str | None, Field(max_length=100)] = None
    required: bool | None = None
    min_length: Annotated[int | None, Field(ge=0, le=4000)] = None
    max_length: Annotated[int | None, Field(ge=1, le=4000)] = None
