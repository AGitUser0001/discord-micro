# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._sticker_format_types import StickerFormatTypes
from ._sticker_types import StickerTypes


class StandardStickerResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    tags: str
    type: StickerTypes
    format_type: StickerFormatTypes | None
    description: str | None
    pack_id: SnowflakeType
    sort_value: int
