# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._allow_list_item import AllowListItem
from ._keyword_filter_item import KeywordFilterItem
from ._regex_pattern import RegexPattern


class KeywordTriggerMetadata(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    keyword_filter: Annotated[
        list[KeywordFilterItem] | None, Field(max_length=1000)
    ] = None
    regex_patterns: Annotated[list[RegexPattern] | None, Field(max_length=10)] = None
    allow_list: Annotated[list[AllowListItem] | None, Field(max_length=100)] = None
