# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIUnavailableGuild(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Guild id')]
    unavailable: Annotated[
        bool, Field(description='`true` if this guild is unavailable due to an outage')
    ]
