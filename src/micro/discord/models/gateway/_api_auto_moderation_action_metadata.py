# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIAutoModerationActionMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: Annotated[
        str | None,
        Field(
            description='Channel to which user content should be logged\n\nAssociated action type: AutoModerationActionType.SendAlertMessage'
        ),
    ] = None
    duration_seconds: Annotated[
        float | None,
        Field(
            description='Timeout duration in seconds (Maximum of 4 weeks - 2419200 seconds)\n\nOnly available if using AutoModerationRuleTriggerType.Keyword\n\nAssociated action type: AutoModerationActionType.Timeout'
        ),
    ] = None
    custom_message: Annotated[
        str | None,
        Field(
            description='Additional explanation that will be shown to members whenever their message is blocked (Maximum 150 characters)\n\nAssociated action type AutoModerationActionType.BlockMessage'
        ),
    ] = None
