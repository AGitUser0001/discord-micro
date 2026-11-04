# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_authorizing_integration_owners_map import APIAuthorizingIntegrationOwnersMap
from ._api_user import APIUser


class APIApplicationCommandInteractionMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the interaction')]
    type: Annotated[Literal[2], Field(description='Type of interaction')]
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
    target_user: Annotated[
        APIUser | None,
        Field(
            description='The user the command was run on, present only on user commands interactions'
        ),
    ] = None
    target_message_id: Annotated[
        str | None,
        Field(
            description='The ID of the message the command was run on, present only on message command interactions.\nThe original response message will also have `message_reference` and `referenced_message` pointing to this message.'
        ),
    ] = None
