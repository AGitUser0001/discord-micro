# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._event_type import EventType
from ._trigger_type import TriggerType
from ._api_auto_moderation_rule_trigger_metadata import APIAutoModerationRuleTriggerMetadata
from ._api_auto_moderation_action import APIAutoModerationAction


class APIAutoModerationRule(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of this rule')]
    guild_id: Annotated[str, Field(description='The guild which this rule belongs to')]
    name: Annotated[str, Field(description='The rule name')]
    creator_id: Annotated[str, Field(description='The user id who created this rule')]
    event_type: Annotated[EventType, Field(description='The rule event type')]
    trigger_type: Annotated[TriggerType, Field(description='The rule trigger type')]
    trigger_metadata: Annotated[
        APIAutoModerationRuleTriggerMetadata,
        Field(description='The rule trigger metadata'),
    ]
    actions: Annotated[
        list[APIAutoModerationAction],
        Field(description='The actions which will execute when this rule is triggered'),
    ]
    enabled: Annotated[bool, Field(description='Whether this rule is enabled')]
    exempt_roles: Annotated[
        list[str],
        Field(
            description="The role ids that shouldn't be affected by this rule (Maximum of 20)"
        ),
    ]
    exempt_channels: Annotated[
        list[str],
        Field(
            description="The channel ids that shouldn't be affected by this rule (Maximum of 50)"
        ),
    ]
