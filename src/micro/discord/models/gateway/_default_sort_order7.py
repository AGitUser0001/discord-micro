# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._default_sort_order7_enum import DefaultSortOrder7Enum


class DefaultSortOrder7(RootModel[DefaultSortOrder7Enum | None]):
    root: Annotated[
        DefaultSortOrder7Enum | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ] = None
