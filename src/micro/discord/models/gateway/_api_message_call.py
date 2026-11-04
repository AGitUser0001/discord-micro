# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIMessageCall(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    participants: Annotated[
        list[str], Field(description='Array of user ids that participated in the call')
    ]
    ended_timestamp: Annotated[
        str | None, Field(description='ISO8601 timestamp when the call ended')
    ] = None
