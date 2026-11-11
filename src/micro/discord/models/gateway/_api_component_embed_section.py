# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_button_component_with_url_type_o1 import APIButtonComponentWithURLTypeO1
from ._api_text_display_component import APITextDisplayComponent
from ._api_button_component_with_url_type import APIButtonComponentWithURLType
from ._api_thumbnail_component import APIThumbnailComponent


class APIComponentEmbedSection(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    accessory: (
        APIThumbnailComponent
        | APIButtonComponentWithURLTypeO1
        | APIButtonComponentWithURLType
    )
    type: Annotated[Literal[9], Field(description='The type of the component')]
    id: Annotated[
        float | None,
        Field(
            description="32 bit integer used as an optional identifier for component\n\nThe id field is optional and is used to identify components in the response from an interaction that aren't interactive components. The id must be unique within the message and is generated sequentially if left empty. Generation of ids won't use another id that exists in the message if you have one defined for another component."
        ),
    ] = None
    components: Annotated[
        list[APITextDisplayComponent], Field(description='One to three text components')
    ]
