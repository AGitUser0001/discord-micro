# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type import Type
from ._role import Role


class APIApplicationCommandPermission(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str,
        Field(
            description='The id of the role, user or channel. Can also be a permission constant'
        ),
    ]
    type: Annotated[Type, Field(description='Role, user or channel')]
    permission: Annotated[
        bool, Field(description='`true` to allow, `false`, to disallow')
    ]
