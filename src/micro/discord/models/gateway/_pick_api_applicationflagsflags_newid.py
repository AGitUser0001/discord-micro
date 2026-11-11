# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags61 import Flags61


class PickAPIApplicationflagsflagsNewid(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the app')]
    flags: Annotated[Flags61, Field(description="The application's public flags")]
    flags_new: Annotated[str, Field(description="The application's public flags")]
