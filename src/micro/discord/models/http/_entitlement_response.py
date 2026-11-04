# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._entitlement_tenant_fulfillment_status_response import EntitlementTenantFulfillmentStatusResponse
from ._entitlement_types import EntitlementTypes
from ._snowflake_type import SnowflakeType


class EntitlementResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    sku_id: SnowflakeType
    application_id: SnowflakeType
    user_id: SnowflakeType
    guild_id: SnowflakeType | None = None
    deleted: bool
    starts_at: AwareDatetime | None
    ends_at: AwareDatetime | None
    type: EntitlementTypes
    fulfilled_at: AwareDatetime | None = None
    fulfillment_status: EntitlementTenantFulfillmentStatusResponse | None = None
    consumed: bool | None = None
    gifter_user_id: SnowflakeType | None = None
    parent_id: SnowflakeType | None = None
