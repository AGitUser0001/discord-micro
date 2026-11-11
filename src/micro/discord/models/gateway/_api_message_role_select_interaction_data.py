# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._required_pick_api_interaction_data_resolvedroles import RequiredPickAPIInteractionDataResolvedroles


class APIMessageRoleSelectInteractionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    custom_id: Annotated[str, Field(description='The `custom_id` of the component')]
    component_type: Annotated[
        Literal[6], Field(description='The type of the component')
    ]
    values: list[str]
    resolved: RequiredPickAPIInteractionDataResolvedroles
