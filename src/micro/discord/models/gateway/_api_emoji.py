# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_user import APIUser


class APIEmoji(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str | None, Field(description='Emoji id')]
    name: Annotated[
        str | None,
        Field(description='Emoji name (can be null only in reaction emoji objects)'),
    ]
    animated: Annotated[
        bool | None, Field(description='Whether this emoji is animated')
    ] = None
    roles: Annotated[
        list[str] | None, Field(description='Roles this emoji is whitelisted to')
    ] = None
    user: Annotated[
        APIUser | None, Field(description='User that created this emoji')
    ] = None
    require_colons: Annotated[
        bool | None, Field(description='Whether this emoji must be wrapped in colons')
    ] = None
    managed: Annotated[
        bool | None, Field(description='Whether this emoji is managed')
    ] = None
    available: Annotated[
        bool | None,
        Field(
            description='Whether this emoji can be used, may be false due to loss of Server Boosts'
        ),
    ] = None
