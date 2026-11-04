# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._string_select_option_for_request import StringSelectOptionForRequest


class StringSelectComponentForMessageRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    custom_id: Annotated[str, Field(max_length=100, min_length=1)]
    placeholder: Annotated[str | None, Field(max_length=150)] = None
    min_values: Annotated[int | None, Field(ge=0, le=25)] = None
    max_values: Annotated[int | None, Field(ge=1, le=25)] = None
    disabled: bool | None = None
    required: bool | None = None
    options: Annotated[
        list[StringSelectOptionForRequest], Field(max_length=25, min_length=1)
    ]
