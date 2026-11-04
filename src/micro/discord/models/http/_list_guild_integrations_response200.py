# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_subscription_integration_response import GuildSubscriptionIntegrationResponse
from ._external_connection_integration_response import ExternalConnectionIntegrationResponse
from ._discord_integration_response import DiscordIntegrationResponse


class ListGuildIntegrationsResponse200(
    RootModel[
        list[
            DiscordIntegrationResponse
            | ExternalConnectionIntegrationResponse
            | GuildSubscriptionIntegrationResponse
        ]
        | None
    ]
):
    root: (
        list[
            DiscordIntegrationResponse
            | ExternalConnectionIntegrationResponse
            | GuildSubscriptionIntegrationResponse
        ]
        | None
    )
