# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._recordstring_api_role import RecordstringAPIRole


class RequiredPickAPIInteractionDataResolvedroles(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    roles: RecordstringAPIRole
