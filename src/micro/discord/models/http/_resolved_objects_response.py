# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ResolvedObjectsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    users: dict[str, Any] | None = None
    members: dict[str, Any] | None = None
    channels: dict[str, Any] | None = None
    roles: dict[str, Any] | None = None
