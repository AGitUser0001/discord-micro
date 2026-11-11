# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._flags import Flags


class CreateOrJoinLobbyRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    idle_timeout_seconds: Annotated[int | None, Field(ge=5, le=604800)] = None
    lobby_metadata: dict[str, Any] | None = None
    member_metadata: dict[str, Any] | None = None
    secret: Annotated[str, Field(max_length=250)]
    flags: Flags | None = None
    name: Annotated[str | None, Field(max_length=100, min_length=1)] = None
