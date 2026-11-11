# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class GetLobbyMessagesParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    limit: Annotated[int | None, Field(ge=1, le=200)] = None
