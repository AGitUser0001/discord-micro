# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type10 import Type10


class APIMessageActivity(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Type10, Field(description='Type of message activity')]
    party_id: Annotated[
        str | None, Field(description='`party_id` from a Rich Presence event')
    ] = None
