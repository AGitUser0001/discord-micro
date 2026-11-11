# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type3 import Type3


class APIEntitlement(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the entitlement')]
    sku_id: Annotated[str, Field(description='ID of the SKU')]
    user_id: Annotated[
        str | None,
        Field(
            description="ID of the user that is granted access to the entitlement's sku"
        ),
    ] = None
    guild_id: Annotated[
        str | None,
        Field(
            description="ID of the guild that is granted access to the entitlement's sku"
        ),
    ] = None
    application_id: Annotated[str, Field(description='ID of the parent application')]
    type: Annotated[Type3, Field(description='Type of entitlement')]
    deleted: Annotated[bool, Field(description='Whether the entitlement was deleted')]
    starts_at: Annotated[
        str | None, Field(description='Start date at which the entitlement is valid.')
    ]
    ends_at: Annotated[
        str | None,
        Field(description='Date at which the entitlement is no longer valid.'),
    ]
    consumed: Annotated[
        bool | None,
        Field(
            description='For consumable items, whether or not the entitlement has been consumed'
        ),
    ] = None
