# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ApplicationIdentityProviderAuthType(StrEnum):
    OIDC = 'OIDC'
    EPIC_ONLINE_SERVICES_ACCESS_TOKEN = 'EPIC_ONLINE_SERVICES_ACCESS_TOKEN'
    EPIC_ONLINE_SERVICES_ID_TOKEN = 'EPIC_ONLINE_SERVICES_ID_TOKEN'
    STEAM_SESSION_TICKET = 'STEAM_SESSION_TICKET'
    UNITY_SERVICES_ID_TOKEN = 'UNITY_SERVICES_ID_TOKEN'
    DISCORD_BOT_ISSUED_ACCESS_TOKEN = 'DISCORD_BOT_ISSUED_ACCESS_TOKEN'
    APPLE_ID_TOKEN = 'APPLE_ID_TOKEN'
    PLAYSTATION_NETWORK_ID_TOKEN = 'PLAYSTATION_NETWORK_ID_TOKEN'
