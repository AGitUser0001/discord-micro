# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._default_sort_order5_enum import DefaultSortOrder5Enum


class DefaultSortOrder5(RootModel[DefaultSortOrder5Enum | None]):
    root: Annotated[
        DefaultSortOrder5Enum | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ] = None
