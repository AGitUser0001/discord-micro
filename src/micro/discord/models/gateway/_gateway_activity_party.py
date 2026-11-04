# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayActivityParty(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str | None, Field(description='The id of the party')] = None
    size: Annotated[
        list[float] | None,
        Field(
            description="Used to show the party's current and maximum size",
            max_length=2,
            min_length=2,
        ),
    ] = None
