# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIApplicationCommandInteractionDataIntegerOptionApplicationCommand(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    type: Literal[4]
    value: float
    focused: bool | None = None
