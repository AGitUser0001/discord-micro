# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_text_display_component import APITextDisplayComponent
from ._api_separator_component import APISeparatorComponent
from ._api_file_component import APIFileComponent
from ._api_media_gallery_component import APIMediaGalleryComponent
from ._api_section_component import APISectionComponent
from ._api_action_row_component_api_component_in_message_action_row import APIActionRowComponentAPIComponentInMessageActionRow
from ._api_container_component import APIContainerComponent


class APIMessageTopLevelComponent(
    RootModel[
        APIActionRowComponentAPIComponentInMessageActionRow
        | APIContainerComponent
        | APIFileComponent
        | APIMediaGalleryComponent
        | APISectionComponent
        | APISeparatorComponent
        | APITextDisplayComponent
    ]
):
    root: Annotated[
        APIActionRowComponentAPIComponentInMessageActionRow
        | APIContainerComponent
        | APIFileComponent
        | APIMediaGalleryComponent
        | APISectionComponent
        | APISeparatorComponent
        | APITextDisplayComponent,
        Field(discriminator='type'),
    ]
