# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIEmbedProvider(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str | None, Field(description='Name of provider')] = None
    url: Annotated[str | None, Field(description='URL of provider')] = None
