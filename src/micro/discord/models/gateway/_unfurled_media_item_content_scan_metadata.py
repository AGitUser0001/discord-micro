# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags41 import Flags41


class UnfurledMediaItemContentScanMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    flags: Annotated[
        Flags41, Field(description='Content scan metadata flags combined as a bitfield')
    ]
