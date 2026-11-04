# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type1 import Type1
from ._api_auto_moderation_action_metadata import APIAutoModerationActionMetadata


class APIAutoModerationAction(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Type1, Field(description='The action type')]
    metadata: Annotated[
        APIAutoModerationActionMetadata | None,
        Field(
            description='Additional metadata needed during execution for this specific action type\n\nWill only be omitted if the action type is AutoModerationActionType.BlockMessage'
        ),
    ] = None
