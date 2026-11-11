# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayIdentifyProperties(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    os: Annotated[str, Field(description='Your operating system')]
    browser: Annotated[str, Field(description='Your library name')]
    device: Annotated[str, Field(description='Your library name')]
