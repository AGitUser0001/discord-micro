# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._separator_component_response import SeparatorComponentResponse
from ._text_display_component_response import TextDisplayComponentResponse
from ._file_component_response import FileComponentResponse
from ._media_gallery_component_response import MediaGalleryComponentResponse
from ._section_component_response import SectionComponentResponse
from ._action_row_component_response import ActionRowComponentResponse


class ContainerComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    accent_color: int | None
    components: list[
        ActionRowComponentResponse
        | FileComponentResponse
        | MediaGalleryComponentResponse
        | SectionComponentResponse
        | SeparatorComponentResponse
        | TextDisplayComponentResponse
    ]
    spoiler: bool
