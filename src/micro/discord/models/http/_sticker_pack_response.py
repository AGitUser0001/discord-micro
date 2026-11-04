# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._standard_sticker_response import StandardStickerResponse


class StickerPackResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    sku_id: SnowflakeType
    name: str
    description: str | None
    stickers: list[StandardStickerResponse]
    cover_sticker_id: SnowflakeType | None = None
    banner_asset_id: SnowflakeType | None = None
