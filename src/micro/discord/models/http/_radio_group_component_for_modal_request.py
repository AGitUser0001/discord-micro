# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._radio_group_option_for_request import RadioGroupOptionForRequest


class RadioGroupComponentForModalRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    custom_id: Annotated[str, Field(max_length=100, min_length=1)]
    required: bool | None = None
    options: Annotated[
        list[RadioGroupOptionForRequest], Field(max_length=10, min_length=2)
    ]
