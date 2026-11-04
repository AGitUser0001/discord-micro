# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._new_value5 import NewValue5
from ._old_value5 import OldValue5


class APIAuditLogChangeKeyFormatType(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['format_type']
    new_value: Annotated[
        NewValue5 | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: OldValue5 | None = None
