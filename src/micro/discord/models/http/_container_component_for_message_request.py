# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._separator_component_for_message_request import SeparatorComponentForMessageRequest
from ._text_display_component_for_message_request import TextDisplayComponentForMessageRequest
from ._file_component_for_message_request import FileComponentForMessageRequest
from ._media_gallery_component_for_message_request import MediaGalleryComponentForMessageRequest
from ._section_component_for_message_request import SectionComponentForMessageRequest
from ._action_row_component_for_message_request import ActionRowComponentForMessageRequest


class ContainerComponentForMessageRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    accent_color: Annotated[int | None, Field(ge=0, le=16777215)] = None
    components: Annotated[
        list[
            ActionRowComponentForMessageRequest
            | FileComponentForMessageRequest
            | MediaGalleryComponentForMessageRequest
            | SectionComponentForMessageRequest
            | SeparatorComponentForMessageRequest
            | TextDisplayComponentForMessageRequest
        ],
        Field(max_length=40, min_length=1),
    ]
    spoiler: bool | None = None
