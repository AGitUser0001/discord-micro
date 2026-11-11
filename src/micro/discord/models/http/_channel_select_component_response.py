# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._channel_types import ChannelTypes
from ._message_component_types import MessageComponentTypes
from ._channel_select_default_value_response import ChannelSelectDefaultValueResponse


class ChannelSelectComponentResponse(DiscordModel):
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
    channel_types: list[ChannelTypes] | None = None
    default_values: list[ChannelSelectDefaultValueResponse] | None = None
