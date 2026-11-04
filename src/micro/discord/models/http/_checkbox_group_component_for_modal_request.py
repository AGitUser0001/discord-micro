# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._checkbox_group_option_for_request import CheckboxGroupOptionForRequest
from ._message_component_types import MessageComponentTypes


class CheckboxGroupComponentForModalRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    custom_id: Annotated[str, Field(max_length=100, min_length=1)]
    min_values: Annotated[int | None, Field(ge=0, le=10)] = None
    max_values: Annotated[int | None, Field(ge=1, le=10)] = None
    required: bool | None = None
    options: Annotated[
        list[CheckboxGroupOptionForRequest], Field(max_length=10, min_length=1)
    ]
