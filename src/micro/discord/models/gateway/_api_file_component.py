# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_unfurled_media_item import APIUnfurledMediaItem


class APIFileComponent(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Literal[13], Field(description='The type of the component')]
    id: Annotated[
        float | None,
        Field(
            description="32 bit integer used as an optional identifier for component\n\nThe id field is optional and is used to identify components in the response from an interaction that aren't interactive components. The id must be unique within the message and is generated sequentially if left empty. Generation of ids won't use another id that exists in the message if you have one defined for another component."
        ),
    ] = None
    file: Annotated[
        APIUnfurledMediaItem,
        Field(
            description='This unfurled media item is unique in that it **only** support attachment references using the `attachment://<filename>` syntax'
        ),
    ]
    spoiler: Annotated[
        bool | None,
        Field(description='Whether the media should be a spoiler (or blurred out)'),
    ] = None
    name: Annotated[
        str | None,
        Field(
            description='The name of the file. This field is ignored and provided by the API as part of the response'
        ),
    ] = None
    size: Annotated[
        float | None,
        Field(
            description='The size of the file in bytes. This field is ignored and provided by the API as part of the response'
        ),
    ] = None
