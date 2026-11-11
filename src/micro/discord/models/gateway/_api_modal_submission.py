# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_modal_submission_component import APIModalSubmissionComponent
from ._api_interaction_data_resolved import APIInteractionDataResolved


class APIModalSubmission(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    resolved: Annotated[
        APIInteractionDataResolved | None,
        Field(
            description="Data for users, members, channels, and roles in the modal's auto-populated select menus"
        ),
    ] = None
    custom_id: Annotated[
        str,
        Field(
            description='A developer-defined identifier for the component, max 100 characters'
        ),
    ]
    components: Annotated[
        list[APIModalSubmissionComponent],
        Field(description='A list of child components'),
    ]
