# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIMessageRoleSubscriptionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    role_subscription_listing_id: Annotated[
        str,
        Field(description='The id of the SKU and listing the user is subscribed to'),
    ]
    tier_name: Annotated[
        str, Field(description='The name of the tier the user is subscribed to')
    ]
    total_months_subscribed: Annotated[
        float,
        Field(description='The number of months the user has been subscribed for'),
    ]
    is_renewal: Annotated[
        bool, Field(description='Whether this notification is for a renewal')
    ]
