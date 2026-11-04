# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._default_sort_order4_enum import DefaultSortOrder4Enum


class DefaultSortOrder4(RootModel[DefaultSortOrder4Enum | None]):
    root: Annotated[
        DefaultSortOrder4Enum | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ] = None
