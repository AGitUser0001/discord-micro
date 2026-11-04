# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._text_display_component_for_message_request import TextDisplayComponentForMessageRequest
from ._thumbnail_component_for_message_request import ThumbnailComponentForMessageRequest
from ._button_component_for_message_request import ButtonComponentForMessageRequest


class SectionComponentForMessageRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    components: Annotated[
        list[TextDisplayComponentForMessageRequest], Field(max_length=3, min_length=1)
    ]
    accessory: ButtonComponentForMessageRequest | ThumbnailComponentForMessageRequest
