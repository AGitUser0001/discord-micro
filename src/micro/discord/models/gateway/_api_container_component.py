# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_component_in_container import APIComponentInContainer


class APIContainerComponent(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Literal[17], Field(description='The type of the component')]
    id: Annotated[
        float | None,
        Field(
            description="32 bit integer used as an optional identifier for component\n\nThe id field is optional and is used to identify components in the response from an interaction that aren't interactive components. The id must be unique within the message and is generated sequentially if left empty. Generation of ids won't use another id that exists in the message if you have one defined for another component."
        ),
    ] = None
    accent_color: Annotated[
        float | None,
        Field(
            description='Color for the accent on the container as RGB from `0x000000` to `0xFFFFFF`'
        ),
    ] = None
    spoiler: Annotated[
        bool | None,
        Field(description='Whether the container should be a spoiler (or blurred out)'),
    ] = None
    components: Annotated[
        list[APIComponentInContainer],
        Field(
            description='Up to 10 components of the type action row, text display, section, media gallery, separator, or file'
        ),
    ]
