# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._default_sort_order_enum import DefaultSortOrderEnum


class DefaultSortOrder(RootModel[DefaultSortOrderEnum | None]):
    root: Annotated[
        DefaultSortOrderEnum | None,
        Field(
            description='The default sort order type used to order posts in a thread-only channel'
        ),
    ] = None
