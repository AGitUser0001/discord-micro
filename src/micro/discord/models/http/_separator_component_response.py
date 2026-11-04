# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_separator_spacing_size import MessageComponentSeparatorSpacingSize
from ._message_component_types import MessageComponentTypes


class SeparatorComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    spacing: MessageComponentSeparatorSpacingSize
    divider: bool
