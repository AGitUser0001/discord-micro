# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._text_display_component_response import TextDisplayComponentResponse
from ._thumbnail_component_response import ThumbnailComponentResponse
from ._button_component_response import ButtonComponentResponse


class SectionComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    components: list[TextDisplayComponentResponse]
    accessory: ButtonComponentResponse | ThumbnailComponentResponse
