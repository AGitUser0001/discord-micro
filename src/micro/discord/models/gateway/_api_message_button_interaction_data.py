# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIMessageButtonInteractionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    custom_id: Annotated[str, Field(description='The `custom_id` of the component')]
    component_type: Annotated[
        Literal[2], Field(description='The type of the component')
    ]
