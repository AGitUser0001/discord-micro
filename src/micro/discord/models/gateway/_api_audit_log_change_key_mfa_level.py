# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._new_value6 import NewValue6
from ._old_value6 import OldValue6


class APIAuditLogChangeKeyMFALevel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['mfa_level']
    new_value: Annotated[
        NewValue6 | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: OldValue6 | None = None
