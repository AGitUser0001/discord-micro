# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_types import ApplicationTypes
from ._snowflake_type import SnowflakeType
from ._application_o_auth2_install_params_response import ApplicationOAuth2InstallParamsResponse
from ._user_response import UserResponse
from ._application_integration_type_configuration_response import ApplicationIntegrationTypeConfigurationResponse


class ApplicationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    icon: str | None
    description: str
    type: ApplicationTypes | None
    cover_image: str | None = None
    primary_sku_id: SnowflakeType | None = None
    bot: UserResponse | None = None
    slug: str | None = None
    guild_id: SnowflakeType | None = None
    rpc_origins: list[str] | None = None
    bot_public: bool | None = None
    bot_require_code_grant: bool | None = None
    terms_of_service_url: AnyUrl | None = None
    privacy_policy_url: AnyUrl | None = None
    custom_install_url: AnyUrl | None = None
    install_params: ApplicationOAuth2InstallParamsResponse | None = None
    integration_types_config: (
        dict[str, ApplicationIntegrationTypeConfigurationResponse] | None
    ) = None
    verify_key: str
    flags: int
    flags_new: str
    max_participants: int | None = None
    tags: list[str] | None = None
