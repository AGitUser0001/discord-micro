# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_role_colors import APIRoleColors
from ._api_role_tags import APIRoleTags


class APIRole(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Role id')]
    name: Annotated[str, Field(description='Role name')]
    color: Annotated[
        float,
        Field(
            deprecated=True,
            description='Integer representation of hexadecimal color code',
        ),
    ]
    colors: Annotated[APIRoleColors, Field(description="The role's colors")]
    hoist: Annotated[
        bool, Field(description='If this role is pinned in the user listing')
    ]
    icon: Annotated[str | None, Field(description='The role icon hash')] = None
    unicode_emoji: Annotated[
        str | None, Field(description='The role unicode emoji as a standard emoji')
    ] = None
    position: Annotated[float, Field(description='Position of this role')]
    permissions: Annotated[str, Field(description='Permission bit set')]
    managed: Annotated[
        bool, Field(description='Whether this role is managed by an integration')
    ]
    mentionable: Annotated[bool, Field(description='Whether this role is mentionable')]
    tags: Annotated[APIRoleTags | None, Field(description='The tags this role has')] = (
        None
    )
    flags: Annotated[Literal[1], Field(description='Role flags')]
