# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._new_value3 import NewValue3
from ._old_value3 import OldValue3


class APIAuditLogChangeKeyExpireBehavior(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['expire_behavior']
    new_value: Annotated[
        NewValue3 | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: OldValue3 | None = None
