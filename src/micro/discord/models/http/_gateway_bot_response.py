# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._gateway_bot_session_start_limit_response import GatewayBotSessionStartLimitResponse


class GatewayBotResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    url: AnyUrl
    session_start_limit: GatewayBotSessionStartLimitResponse
    shards: int
