# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIApplicationCommandInteractionDataIntegerOptionApplicationCommandAutocomplete(
    BaseModel
):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    type: Literal[4]
    value: str
    focused: bool | None = None
