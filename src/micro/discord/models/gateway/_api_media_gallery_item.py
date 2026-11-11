# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_unfurled_media_item import APIUnfurledMediaItem


class APIMediaGalleryItem(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    media: Annotated[APIUnfurledMediaItem, Field(description='A url or attachment')]
    description: Annotated[str | None, Field(description='Alt text for the media')] = (
        None
    )
    spoiler: Annotated[
        bool | None,
        Field(description='Whether the media should be a spoiler (or blurred out)'),
    ] = None
