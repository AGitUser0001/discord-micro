# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._subscription_response_status_type import SubscriptionResponseStatusType


class SubscriptionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[SnowflakeType, Field(description='ID of the subscription')]
    user_id: Annotated[
        SnowflakeType, Field(description='ID of the user who is subscribed')
    ]
    sku_ids: Annotated[
        list[SnowflakeType], Field(description='List of SKUs subscribed to')
    ]
    renewal_sku_ids: Annotated[
        list[SnowflakeType] | None,
        Field(
            description='List of SKUs that this user will be subscribed to at renewal'
        ),
    ]
    entitlement_ids: Annotated[
        list[SnowflakeType],
        Field(description='List of entitlements granted for this subscription'),
    ]
    current_period_start: Annotated[
        AwareDatetime, Field(description='Start of the current subscription period')
    ]
    current_period_end: Annotated[
        AwareDatetime, Field(description='End of the current subscription period')
    ]
    status: Annotated[
        SubscriptionResponseStatusType,
        Field(description='Current status of the subscription'),
    ]
    canceled_at: Annotated[
        AwareDatetime | None, Field(description='When the subscription was canceled')
    ]
    country: Annotated[
        str | None,
        Field(
            description='ISO3166-1 alpha-2 country code of the payment source used to purchase the subscription'
        ),
    ] = None
