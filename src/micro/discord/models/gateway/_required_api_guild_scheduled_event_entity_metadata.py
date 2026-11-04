# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class RequiredAPIGuildScheduledEventEntityMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    location: Annotated[str, Field(description='The location of the scheduled event')]
