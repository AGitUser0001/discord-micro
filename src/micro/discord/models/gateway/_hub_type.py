# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._hub_type_enum import HubTypeEnum


class HubType(RootModel[HubTypeEnum | None]):
    root: Annotated[
        HubTypeEnum | None, Field(description='The type of Student Hub the guild is')
    ] = None
