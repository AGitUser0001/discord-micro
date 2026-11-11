# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._string_select_option_response import StringSelectOptionResponse


class StringSelectComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    custom_id: str
    placeholder: str | None = None
    min_values: int
    max_values: int
    disabled: bool | None = None
    options: list[StringSelectOptionResponse]
