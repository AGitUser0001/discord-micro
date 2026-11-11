# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._default_sort_order3_enum import DefaultSortOrder3Enum


class DefaultSortOrder3(RootModel[DefaultSortOrder3Enum | None]):
    root: Annotated[
        DefaultSortOrder3Enum | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ] = None
