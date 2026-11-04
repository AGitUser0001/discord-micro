# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._default_sort_order1_enum import DefaultSortOrder1Enum


class DefaultSortOrder1(RootModel[DefaultSortOrder1Enum | None]):
    root: Annotated[
        DefaultSortOrder1Enum | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ] = None
