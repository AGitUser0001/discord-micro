# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_text_display_component import APITextDisplayComponent
from ._api_section_accessory_component import APISectionAccessoryComponent


class APISectionComponent(BaseModel):
    model_config = ConfigDict(
        extra='allow',
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
    accessory: Annotated[
        APISectionAccessoryComponent,
        Field(
            description='A thumbnail or a button component, with a future possibility of adding more compatible components'
        ),
    ]
