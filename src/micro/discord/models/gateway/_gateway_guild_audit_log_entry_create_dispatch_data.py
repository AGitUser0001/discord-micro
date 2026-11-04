# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._action_type import ActionType
from ._api_audit_log_options import APIAuditLogOptions
from ._api_audit_log_change import APIAuditLogChange


class GatewayGuildAuditLogEntryCreateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    target_id: Annotated[
        str | None,
        Field(description='ID of the affected entity (webhook, user, role, etc.)'),
    ]
    changes: Annotated[
        list[APIAuditLogChange] | None,
        Field(description='Changes made to the `target_id`'),
    ] = None
    user_id: Annotated[
        str | None,
        Field(
            description='The user who made the changes\n\nThis can be `null` in some cases (webhooks deleting themselves by using their own token, for example)'
        ),
    ]
    id: Annotated[str, Field(description='ID of the entry')]
    action_type: Annotated[
        ActionType, Field(description='Type of action that occurred')
    ]
    options: Annotated[
        APIAuditLogOptions | None,
        Field(description='Additional info for certain action types'),
    ] = None
    reason: Annotated[
        str | None, Field(description='The reason for the change (0-512 characters)')
    ] = None
    guild_id: Annotated[str, Field(description='ID of the guild')]
