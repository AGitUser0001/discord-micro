# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class MessageRoleSubscriptionDataResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    role_subscription_listing_id: SnowflakeType
    tier_name: str
    total_months_subscribed: int
    is_renewal: bool
