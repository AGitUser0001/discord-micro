# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_user_interaction_data_resolved import APIUserInteractionDataResolved


class APIMessageUserSelectInteractionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    custom_id: Annotated[str, Field(description='The `custom_id` of the component')]
    component_type: Annotated[
        Literal[5], Field(description='The type of the component')
    ]
    values: list[str]
    resolved: APIUserInteractionDataResolved
