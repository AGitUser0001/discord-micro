# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._account_response import AccountResponse
from ._integration_types import IntegrationTypes
from ._connected_account_guild_response import ConnectedAccountGuildResponse


class ConnectedAccountIntegrationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: str
    type: IntegrationTypes
    account: AccountResponse
    guild: ConnectedAccountGuildResponse
