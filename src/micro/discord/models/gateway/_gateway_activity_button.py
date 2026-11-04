# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayActivityButton(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    label: Annotated[
        str, Field(description='The text shown on the button (1-32 characters)')
    ]
    url: Annotated[
        str,
        Field(description='The url opened when clicking the button (1-512 characters)'),
    ]
