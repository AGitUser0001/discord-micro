# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._account_response import AccountResponse
from ._integration_types import IntegrationTypes
from ._o_auth2_scopes import OAuth2Scopes
from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse
from ._integration_application_response import IntegrationApplicationResponse


class DiscordIntegrationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: IntegrationTypes
    name: str | None
    account: AccountResponse
    enabled: bool
    id: SnowflakeType
    application: IntegrationApplicationResponse
    scopes: list[OAuth2Scopes]
    user: UserResponse | None = None
