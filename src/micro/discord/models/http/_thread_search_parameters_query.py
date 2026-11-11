# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._sorting_order import SortingOrder
from ._thread_search_tag_setting import ThreadSearchTagSetting
from ._thread_sorting_mode import ThreadSortingMode
from ._tag1 import Tag1


class ThreadSearchParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str | None, Field(max_length=100)] = None
    slop: Annotated[int | None, Field(ge=0, le=100)] = None
    min_id: SnowflakeType | None = None
    max_id: SnowflakeType | None = None
    tag: str | Tag1 | None = None
    tag_setting: ThreadSearchTagSetting | None = None
    archived: bool | None = None
    sort_by: ThreadSortingMode | None = None
    sort_order: SortingOrder | None = None
    limit: Annotated[int | None, Field(ge=1, le=25)] = None
    offset: Annotated[int | None, Field(ge=0, le=9975)] = None
