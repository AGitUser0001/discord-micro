# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._scope import Scope


class APIApplicationInstallParams(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    scopes: list[Scope]
    permissions: str
