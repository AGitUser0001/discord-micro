# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_auto_moderation_rule_trigger_metadata import APIAutoModerationRuleTriggerMetadata


class APIAuditLogChangeKeyTriggerMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['trigger_metadata']
    new_value: Annotated[
        APIAutoModerationRuleTriggerMetadata | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: APIAutoModerationRuleTriggerMetadata | None = None
