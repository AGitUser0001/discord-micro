# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type5 import Type5
from ._format_type import FormatType
from ._api_user import APIUser


class APISticker(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the sticker')]
    pack_id: Annotated[
        str | None,
        Field(description='For standard stickers, ID of the pack the sticker is from'),
    ] = None
    name: Annotated[str, Field(description='Name of the sticker')]
    description: Annotated[str | None, Field(description='Description of the sticker')]
    tags: Annotated[
        str,
        Field(
            description="For guild stickers, the Discord name of a unicode emoji representing the sticker's expression. for standard stickers, a comma-separated list of related expressions."
        ),
    ]
    asset: Annotated[
        Literal[''] | None,
        Field(
            deprecated=True,
            description='Previously the sticker asset hash, now an empty string',
        ),
    ] = None
    type: Annotated[Type5, Field(description='Type of sticker')]
    format_type: Annotated[FormatType, Field(description='Type of sticker format')]
    available: Annotated[
        bool | None,
        Field(
            description='Whether this guild sticker can be used, may be false due to loss of Server Boosts'
        ),
    ] = None
    guild_id: Annotated[
        str | None, Field(description='ID of the guild that owns this sticker')
    ] = None
    user: Annotated[
        APIUser | None, Field(description='The user that uploaded the guild sticker')
    ] = None
    sort_value: Annotated[
        float | None,
        Field(description="The standard sticker's sort order within its pack"),
    ] = None
