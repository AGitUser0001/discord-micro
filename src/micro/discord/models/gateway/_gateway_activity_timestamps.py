# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayActivityTimestamps(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    start: Annotated[
        float | None,
        Field(description='Unix time (in milliseconds) of when the activity started'),
    ] = None
    end: Annotated[
        float | None,
        Field(description='Unix time (in milliseconds) of when the activity ends'),
    ] = None
