# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._automod_keyword_preset_type import AutomodKeywordPresetType
from ._allow_list_item import AllowListItem


class DefaultKeywordListTriggerMetadata(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    allow_list: Annotated[list[AllowListItem] | None, Field(max_length=1000)] = None
    presets: list[AutomodKeywordPresetType] | None = None
