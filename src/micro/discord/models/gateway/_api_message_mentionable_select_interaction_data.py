# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._pick_api_interaction_data_resolvedmembersrolesusers import PickAPIInteractionDataResolvedmembersrolesusers


class APIMessageMentionableSelectInteractionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    custom_id: Annotated[str, Field(description='The `custom_id` of the component')]
    component_type: Annotated[
        Literal[7], Field(description='The type of the component')
    ]
    values: list[str]
    resolved: PickAPIInteractionDataResolvedmembersrolesusers
