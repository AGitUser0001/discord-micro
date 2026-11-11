# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type21 import Type21


class GatewayActivityUpdateData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(description="The activity's name")]
    type: Annotated[Type21, Field(description='Activity type')]
    url: Annotated[
        str | None, Field(description='Stream url, is validated when type is `1`')
    ] = None
    state: Annotated[
        str | None,
        Field(
            description="The user's current party status, or the text used for a custom status"
        ),
    ] = None
