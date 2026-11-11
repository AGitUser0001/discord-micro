# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._component_emoji_for_request import ComponentEmojiForRequest


class StringSelectOptionForRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    label: Annotated[str, Field(max_length=100, min_length=1)]
    value: Annotated[str, Field(max_length=100, min_length=1)]
    description: Annotated[str | None, Field(max_length=100)] = None
    default: bool | None = None
    emoji: ComponentEmojiForRequest | None = None
