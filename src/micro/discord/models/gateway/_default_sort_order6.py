# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._default_sort_order6_enum import DefaultSortOrder6Enum


class DefaultSortOrder6(RootModel[DefaultSortOrder6Enum | None]):
    root: Annotated[
        DefaultSortOrder6Enum | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ] = None
