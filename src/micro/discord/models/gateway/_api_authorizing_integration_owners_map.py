# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIAuthorizingIntegrationOwnersMap(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    field_0: Annotated[str | None, Field(alias='0')] = None
    field_1: Annotated[str | None, Field(alias='1')] = None
