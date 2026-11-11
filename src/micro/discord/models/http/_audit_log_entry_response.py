# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._audit_log_action_types import AuditLogActionTypes
from ._audit_log_object_change_response import AuditLogObjectChangeResponse
from ._snowflake_type import SnowflakeType


class AuditLogEntryResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    action_type: AuditLogActionTypes
    user_id: SnowflakeType | None
    target_id: SnowflakeType | None
    changes: list[AuditLogObjectChangeResponse] | None = None
    options: dict[str, str] | None = None
    reason: str | None = None
