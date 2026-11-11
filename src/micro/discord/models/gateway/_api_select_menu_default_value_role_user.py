# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type13 import Type13


class APISelectMenuDefaultValueRoleUser(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Type13
    id: str
