# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._account_response import AccountResponse
from ._integration_expire_behavior_types import IntegrationExpireBehaviorTypes
from ._integration_expire_grace_period_types import IntegrationExpireGracePeriodTypes
from ._integration_types import IntegrationTypes
from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse


class ExternalConnectionIntegrationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: IntegrationTypes
    name: str | None
    account: AccountResponse
    enabled: bool
    id: str
    user: UserResponse
    revoked: bool | None = None
    expire_behavior: IntegrationExpireBehaviorTypes | None = None
    expire_grace_period: IntegrationExpireGracePeriodTypes | None = None
    subscriber_count: int | None = None
    synced_at: AwareDatetime | None = None
    role_id: SnowflakeType | None = None
    syncing: bool | None = None
    enable_emoticons: bool | None = None
