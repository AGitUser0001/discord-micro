# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_authorizing_integration_owners_map import APIAuthorizingIntegrationOwnersMap
from ._api_user import APIUser


class APIMessageComponentInteractionMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the interaction')]
    type: Annotated[Literal[3], Field(description='Type of interaction')]
    user: Annotated[APIUser, Field(description='User who triggered the interaction')]
    authorizing_integration_owners: Annotated[
        APIAuthorizingIntegrationOwnersMap,
        Field(description='IDs for installation context(s) related to an interaction'),
    ]
    original_response_message_id: Annotated[
        str | None,
        Field(
            description='ID of the original response message, present only on follow-up messages'
        ),
    ] = None
    interacted_message_id: Annotated[
        str,
        Field(description='ID of the message that contained the interactive component'),
    ]
