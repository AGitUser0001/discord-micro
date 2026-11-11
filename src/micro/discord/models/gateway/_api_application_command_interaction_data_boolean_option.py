# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIApplicationCommandInteractionDataBooleanOption(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    type: Literal[5]
    value: bool
