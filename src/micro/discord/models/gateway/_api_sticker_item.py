# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._format_type import FormatType


class APIStickerItem(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the sticker')]
    name: Annotated[str, Field(description='Name of the sticker')]
    format_type: Annotated[FormatType, Field(description='Type of sticker format')]
