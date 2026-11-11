# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._status5 import Status5


class APISubscription(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the subscription')]
    user_id: Annotated[str, Field(description='ID of the user who is subscribed')]
    sku_ids: Annotated[list[str], Field(description='List of SKUs subscribed to')]
    entitlement_ids: Annotated[
        list[str],
        Field(description='List of entitlements granted for this subscription'),
    ]
    renewal_sku_ids: Annotated[
        list[str] | None,
        Field(
            description='List of SKUs that this user will be subscribed to at renewal'
        ),
    ]
    current_period_start: Annotated[
        str, Field(description='Start of the current subscription period')
    ]
    current_period_end: Annotated[
        str, Field(description='End of the current subscription period')
    ]
    status: Annotated[Status5, Field(description='Current status of the subscription')]
    canceled_at: Annotated[
        str | None, Field(description='When the subscription was canceled')
    ]
    country: Annotated[
        str | None,
        Field(
            description='ISO3166-1 alpha-2 country code of the payment source used to purchase the subscription. Missing unless queried with a private OAuth scope.'
        ),
    ] = None
