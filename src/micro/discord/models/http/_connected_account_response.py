# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._connected_account_providers import ConnectedAccountProviders
from ._connected_account_visibility import ConnectedAccountVisibility
from ._connected_account_integration_response import ConnectedAccountIntegrationResponse


class ConnectedAccountResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: str
    name: str | None
    type: ConnectedAccountProviders
    friend_sync: bool
    integrations: list[ConnectedAccountIntegrationResponse] | None = None
    show_activity: bool
    two_way_link: bool
    verified: bool
    visibility: ConnectedAccountVisibility
    revoked: bool | None = None
