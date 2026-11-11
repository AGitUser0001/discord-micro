# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_identity_provider_auth_type import ApplicationIdentityProviderAuthType
from ._snowflake_type import SnowflakeType


class PartnerSdkUnmergeProvisionalAccountRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    client_id: SnowflakeType
    client_secret: Annotated[str | None, Field(max_length=1024)] = None
    external_auth_token: Annotated[str, Field(max_length=10240, min_length=1)]
    external_auth_type: ApplicationIdentityProviderAuthType
