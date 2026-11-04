# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._pick_api_roleidname import PickAPIRoleidname


class APIAuditLogChangeKeyX24AddX82E963BA7969E0E4(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    key: Literal['$add']
    new_value: Annotated[
        list[PickAPIRoleidname] | None,
        Field(
            description='The new value\n\nIf `new_value` is not present in the change object, while `old_value` is,\nthat means the property that was changed has been reset, or set to `null`'
        ),
    ] = None
    old_value: list[PickAPIRoleidname] | None = None
