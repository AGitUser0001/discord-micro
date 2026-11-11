# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._new_value7 import NewValue7
from ._old_value7 import OldValue7


class APIAuditLogChangeKeyPrivacyLevel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['privacy_level']
    new_value: Annotated[
        NewValue7 | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: OldValue7 | None = None
