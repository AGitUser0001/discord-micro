# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIReactionCountDetails(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    burst: Annotated[float, Field(description='Count of super reactions')]
    normal: Annotated[float, Field(description='Count of normal reactions')]
