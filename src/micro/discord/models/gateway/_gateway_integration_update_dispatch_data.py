# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._expire_behavior import ExpireBehavior
from ._scope import Scope
from ._api_guild_integration_type import APIGuildIntegrationType
from ._api_integration_account import APIIntegrationAccount
from ._api_user import APIUser
from ._api_guild_integration_application import APIGuildIntegrationApplication


class GatewayIntegrationUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Integration id')]
    name: Annotated[str, Field(description='Integration name')]
    type: Annotated[APIGuildIntegrationType, Field(description='Integration type')]
    enabled: Annotated[bool, Field(description='Is this integration enabled')]
    syncing: Annotated[
        bool | None,
        Field(
            description='Is this integration syncing\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    role_id: Annotated[
        str | None,
        Field(
            description='ID that this integration uses for "subscribers"\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    enable_emoticons: Annotated[
        bool | None,
        Field(
            description='Whether emoticons should be synced for this integration (`twitch` only currently)\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    expire_behavior: Annotated[
        ExpireBehavior | None,
        Field(
            description='The behavior of expiring subscribers\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    expire_grace_period: Annotated[
        float | None,
        Field(
            description='The grace period (in days) before expiring subscribers\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    user: Annotated[
        APIUser | None,
        Field(
            description='User for this integration\n\n**Some older integrations may not have an attached user.**'
        ),
    ] = None
    account: Annotated[
        APIIntegrationAccount, Field(description='Integration account information')
    ]
    synced_at: Annotated[
        str | None,
        Field(
            description='When this integration was last synced\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    subscriber_count: Annotated[
        float | None,
        Field(
            description='How many subscribers this integration has\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    revoked: Annotated[
        bool | None,
        Field(
            description='Has this integration been revoked\n\n**This field is not provided for `discord` bot integrations.**'
        ),
    ] = None
    application: Annotated[
        APIGuildIntegrationApplication | None,
        Field(description='The bot/OAuth2 application for discord integrations'),
    ] = None
    scopes: Annotated[
        list[Scope] | None,
        Field(description='The scopes the application has been authorized for'),
    ] = None
    guild_id: str
