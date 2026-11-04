# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ListPinsParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    before: AwareDatetime | None = None
    limit: Annotated[int | None, Field(ge=1, le=50)] = None
