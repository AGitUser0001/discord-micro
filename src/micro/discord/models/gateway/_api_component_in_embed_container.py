# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_text_display_component import APITextDisplayComponent
from ._api_separator_component import APISeparatorComponent
from ._api_media_gallery_component import APIMediaGalleryComponent
from ._api_action_row_component_api_component_embed_button import APIActionRowComponentAPIComponentEmbedButton
from ._api_component_embed_section import APIComponentEmbedSection


class APIComponentInEmbedContainer(
    RootModel[
        APIActionRowComponentAPIComponentEmbedButton
        | APIComponentEmbedSection
        | APIMediaGalleryComponent
        | APISeparatorComponent
        | APITextDisplayComponent
    ]
):
    root: Annotated[
        APIActionRowComponentAPIComponentEmbedButton
        | APIComponentEmbedSection
        | APIMediaGalleryComponent
        | APISeparatorComponent
        | APITextDisplayComponent,
        Field(discriminator='type'),
    ]
