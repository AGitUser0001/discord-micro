# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._rule_trigger_type import RuleTriggerType
from ._api_auto_moderation_action import APIAutoModerationAction


class GatewayAutoModerationActionExecutionDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[
        str, Field(description='The id of the guild in which action was executed')
    ]
    action: Annotated[
        APIAutoModerationAction, Field(description='The action which was executed')
    ]
    rule_id: Annotated[
        str, Field(description='The id of the rule which action belongs to')
    ]
    rule_trigger_type: Annotated[
        RuleTriggerType,
        Field(description='The trigger type of rule which was triggered'),
    ]
    user_id: Annotated[
        str,
        Field(
            description='The id of the user which generated the content which triggered the rule'
        ),
    ]
    channel_id: Annotated[
        str | None,
        Field(description='The id of the channel in which user content was posted'),
    ] = None
    message_id: Annotated[
        str | None,
        Field(
            description='The id of any user message which content belongs to\n\nThis field will not be present if message was blocked by AutoMod or content was not part of any message'
        ),
    ] = None
    alert_system_message_id: Annotated[
        str | None,
        Field(
            description='The id of any system auto moderation messages posted as a result of this action\n\nThis field will not be present if this event does not correspond to an action with type AutoModerationActionType.SendAlertMessage'
        ),
    ] = None
    content: Annotated[
        str,
        Field(
            description='The user generated text content\n\n`MESSAGE_CONTENT` (`1 << 15`) gateway intent is required to receive non-empty values from this field'
        ),
    ]
    matched_keyword: Annotated[
        str | None,
        Field(
            description='The word or phrase configured in the rule that triggered the rule'
        ),
    ]
    matched_content: Annotated[
        str | None,
        Field(
            description='The substring in content that triggered the rule\n\n`MESSAGE_CONTENT` (`1 << 15`) gateway intent is required to receive non-empty values from this field'
        ),
    ]
