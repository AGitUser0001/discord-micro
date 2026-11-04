# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type2 import Type2


class APIOverwrite(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Role or user id')]
    type: Annotated[Type2, Field(description='Either 0 (role) or 1 (member)')]
    allow: Annotated[str, Field(description='Permission bit set')]
    deny: Annotated[str, Field(description='Permission bit set')]
