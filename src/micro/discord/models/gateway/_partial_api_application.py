# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags39 import Flags39
from ._event_webhooks_status import EventWebhooksStatus
from ._event_webhooks_type import EventWebhooksType
from ._api_application_install_params import APIApplicationInstallParams
from ._api_partial_guild import APIPartialGuild
from ._api_application_integration_types_config_map import APIApplicationIntegrationTypesConfigMap
from ._api_user import APIUser
from ._api_team import APITeam


class PartialAPIApplication(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str | None, Field(description='The id of the app')] = None
    name: Annotated[str | None, Field(description='The name of the app')] = None
    icon: Annotated[str | None, Field(description='The icon hash of the app')] = None
    description: Annotated[
        str | None, Field(description='The description of the app')
    ] = None
    rpc_origins: Annotated[
        list[str] | None,
        Field(description='An array of rpc origin urls, if rpc is enabled'),
    ] = None
    bot_public: Annotated[
        bool | None,
        Field(
            description="When `false` only app owner can join the app's bot to guilds"
        ),
    ] = None
    bot_require_code_grant: Annotated[
        bool | None,
        Field(
            description="When `true` the app's bot will only join upon completion of the full oauth2 code grant flow"
        ),
    ] = None
    bot: Annotated[
        APIUser | None,
        Field(
            description='Partial user object for the bot user associated with the application'
        ),
    ] = None
    terms_of_service_url: Annotated[
        str | None, Field(description="The url of the application's terms of service")
    ] = None
    privacy_policy_url: Annotated[
        str | None, Field(description="The url of the application's privacy policy")
    ] = None
    owner: Annotated[
        APIUser | None,
        Field(
            description='Partial user object containing info on the owner of the application'
        ),
    ] = None
    summary: Annotated[
        Literal[''] | None, Field(deprecated=True, description='An empty string')
    ] = None
    verify_key: Annotated[
        str | None,
        Field(
            description="The hexadecimal encoded key for verification in interactions and the GameSDK's GetTicket function"
        ),
    ] = None
    team: Annotated[
        APITeam | None, Field(description='The team this application belongs to')
    ] = None
    guild_id: Annotated[
        str | None,
        Field(
            description='If this application is a game sold on Discord, this field will be the guild to which it has been linked'
        ),
    ] = None
    guild: Annotated[
        APIPartialGuild | None,
        Field(description='A partial object of the associated guild'),
    ] = None
    primary_sku_id: Annotated[
        str | None,
        Field(
            description='If this application is a game sold on Discord, this field will be the id of the "Game SKU" that is created, if exists'
        ),
    ] = None
    slug: Annotated[
        str | None,
        Field(
            description='If this application is a game sold on Discord, this field will be the URL slug that links to the store page'
        ),
    ] = None
    cover_image: Annotated[
        str | None,
        Field(
            description='If this application is a game sold on Discord, this field will be the hash of the image on store embeds'
        ),
    ] = None
    flags: Annotated[
        Flags39 | None, Field(description="The application's public flags")
    ] = None
    flags_new: Annotated[
        str | None, Field(description="The application's public flags")
    ] = None
    approximate_guild_count: Annotated[
        float | None,
        Field(
            description='Approximate count of guilds the application has been added to'
        ),
    ] = None
    approximate_user_install_count: Annotated[
        float | None,
        Field(
            description='Approximate count of users that have installed the app (authorized with `application.commands` as a scope)'
        ),
    ] = None
    approximate_user_authorization_count: Annotated[
        float | None,
        Field(
            description='Approximate count of users that have OAuth2 authorizations for the app'
        ),
    ] = None
    redirect_uris: Annotated[
        list[str] | None,
        Field(description='Array of redirect URIs for the application'),
    ] = None
    interactions_endpoint_url: Annotated[
        str | None,
        Field(description='The interactions endpoint URL for the application'),
    ] = None
    role_connections_verification_url: Annotated[
        str | None,
        Field(
            description="The application's role connection verification entry point,\nwhich when configured will render the app as a verification method in the guild role verification configuration"
        ),
    ] = None
    tags: Annotated[
        list[str] | None,
        Field(
            description='Up to 5 tags of max 20 characters each describing the content and functionality of the application',
            max_length=5,
            min_length=1,
        ),
    ] = None
    install_params: Annotated[
        APIApplicationInstallParams | None,
        Field(
            description="Settings for the application's default in-app authorization link, if enabled"
        ),
    ] = None
    integration_types_config: Annotated[
        APIApplicationIntegrationTypesConfigMap | None,
        Field(
            description='Default scopes and permissions for each supported installation context. Value for each key is an integration type configuration object'
        ),
    ] = None
    custom_install_url: Annotated[
        str | None,
        Field(
            description="The application's default custom authorization link, if enabled"
        ),
    ] = None
    event_webhooks_url: Annotated[
        str | None,
        Field(description='Event webhook URL for the app to receive webhook events'),
    ] = None
    event_webhooks_status: Annotated[
        EventWebhooksStatus | None,
        Field(description='If webhook events are enabled for the app'),
    ] = None
    event_webhooks_types: Annotated[
        list[EventWebhooksType] | None,
        Field(description='List of webhook event types the app subscribes to'),
    ] = None
