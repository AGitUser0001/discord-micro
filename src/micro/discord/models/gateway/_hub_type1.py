# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._hub_type1_enum import HubType1Enum


class HubType1(RootModel[HubType1Enum | None]):
    root: Annotated[
        HubType1Enum | None, Field(description='The type of Student Hub the guild is')
    ] = None
