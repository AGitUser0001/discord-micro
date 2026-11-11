# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._action_types import ActionTypes
from ._application_event_webhooks_status import ApplicationEventWebhooksStatus
from ._application_explicit_content_filter_types import ApplicationExplicitContentFilterTypes
from ._application_types import ApplicationTypes
from ._o_auth2_scopes import OAuth2Scopes
from ._snowflake_type import SnowflakeType
from ._application_o_auth2_install_params_response import ApplicationOAuth2InstallParamsResponse
from ._user_response import UserResponse
from ._application_integration_type_configuration_response import ApplicationIntegrationTypeConfigurationResponse
from ._team_response import TeamResponse


class PrivateApplicationResponse(DiscordModel):
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
    flags: int
    flags_new: str
    bot: UserResponse | None = None
    slug: str | None = None
    conjure_project_id: SnowflakeType | None = None
    vibegrations_project_id: SnowflakeType | None = None
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
    max_participants: int | None = None
    tags: list[str] | None = None
    redirect_uris: list[AnyUrl]
    interactions_endpoint_url: AnyUrl | None
    role_connections_verification_url: AnyUrl | None
    owner: UserResponse
    approximate_guild_count: int
    approximate_user_install_count: int
    approximate_user_authorization_count: int
    event_webhooks_url: AnyUrl | None = None
    event_webhooks_status: ApplicationEventWebhooksStatus | None = None
    event_webhooks_types: list[ActionTypes] | None = None
    explicit_content_filter: ApplicationExplicitContentFilterTypes
    team: TeamResponse | None
    eligible_oauth2_scopes: list[OAuth2Scopes]
