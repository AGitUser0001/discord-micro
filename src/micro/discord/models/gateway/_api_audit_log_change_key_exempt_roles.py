# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIAuditLogChangeKeyExemptRoles(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['exempt_roles']
    new_value: Annotated[
        list[str] | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: list[str] | None = None
