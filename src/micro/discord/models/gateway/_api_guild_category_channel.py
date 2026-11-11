# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_overwrite import APIOverwrite
from ._flags43 import Flags43


class APIGuildCategoryChannel(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    type: Annotated[
        Literal[4],
        Field(description='An organizational category that contains up to 50 channels'),
    ]
    flags: Flags43 | None = None
    position: Annotated[float, Field(description='Sorting position of the channel')]
    name: Annotated[
        str, Field(description='The name of the channel (1-100 characters)')
    ]
    guild_id: Annotated[
        str | None,
        Field(
            description='The id of the guild (may be missing for some channel objects received over gateway guild dispatches)'
        ),
    ] = None
    permission_overwrites: Annotated[
        list[APIOverwrite] | None,
        Field(description='Explicit permission overwrites for members and roles'),
    ] = None
    nsfw: Annotated[bool | None, Field(description='Whether the channel is nsfw')] = (
        None
    )
    parent_id: Annotated[None, Field(None)] = None
