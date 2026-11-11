# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._new_value2 import NewValue2
from ._old_value2 import OldValue2


class APIAuditLogChangeKeyEventType(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['event_type']
    new_value: Annotated[
        NewValue2 | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: OldValue2 | None = None
