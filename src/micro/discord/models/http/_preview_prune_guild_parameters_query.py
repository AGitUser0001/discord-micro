# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._include_roles1 import IncludeRoles1


class PreviewPruneGuildParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    days: Annotated[int | None, Field(ge=1, le=30)] = None
    include_roles: str | IncludeRoles1 | None = None
